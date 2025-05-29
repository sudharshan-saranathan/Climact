import logging
from PyQt6.QtWidgets import QApplication

# Class ActionsManager - Manages application-wide undo/redo stacks
class ActionsManager:

    # Undo-actions limit:
    MAX_UNDO = 3

    # Initializer:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    # Execute actions:
    def do(self, actions):

        # Prune stacks BEFORE performing actions. Otherwise, if the (MAX_UNDO + 1)^th command is a delete operation of
        # the object in the first action, the object will be removed from the scene BEFORE pruning. Thus, the prune
        # method will see that this object no longer belongs to a scene and delete it, making the last action no longer
        # undoable and crash the application.
        self.prune_undo()
        self.prune_redo()

        actions.execute()                   # Execute command
        self.undo_stack.append(actions)     # Add operation to undo-stack

    # Undo the most recent operation:
    def undo(self):

        # Return if stack is empty:
        if not self.undo_stack:
            logging.info(f"Undo-stack limit reached!")
            QApplication.beep()
            return

        actions = self.undo_stack.pop()     # Pop the most recent command
        actions.undo()                      # Execute undo operation
        self.redo_stack.append(actions)     # Add operation to redo-stack

    # Redo the most recent operation:
    def redo(self):

        # Return if stack is empty:
        if not self.redo_stack:
            logging.info(f"Redo-stack limit reached!")
            QApplication.beep()
            return

        actions = self.redo_stack.pop()     # Pop the most recent command
        actions.redo()                      # Execute redo command
        self.undo_stack.append(actions)     # Add operation to undo-stack

    # Prune undo stack:
    def prune_undo(self):

        # Prune actions older than MAX_UNDO turns:
        while len(self.undo_stack) > ActionsManager.MAX_UNDO:
            to_be_purged = self.undo_stack.pop(0)   # Pop the oldest command:
            to_be_purged.cleanup()                  # Delete items

    # Clears redo stack with every do-operation:
    def prune_redo(self):

        while len(self.redo_stack):
            to_be_purged = self.redo_stack.pop(0)   # Pop the oldest command
            to_be_purged.cleanup()                  # Delete items

    # Clears undo and redo stacks, deletes resources:
    def wipe_stack(self):

        # Safe-delete all previous actions:
        while len(self.undo_stack):
            to_be_purged = self.undo_stack.pop(0)   # Pop the oldest command:
            to_be_purged.cleanup()                  # Delete items

        self.prune_redo()