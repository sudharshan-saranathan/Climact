"""
manager.py
"""
import logging
from PyQt6.QtWidgets import QApplication

# Class ActionsManager - Manages application-wide undo/redo stacks
class ActionsManager:
    """
    This class manages the undo and redo stacks for actions performed in the application.
    """
    # Undo-actions limit:
    MAX_UNDO = 3

    # Initializer:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    # Execute actions:
    def do(self, actions):
        """
        Executes the given actions and adds them to the undo stack. Before executing, it prunes the undo and redo stacks.
        :param actions:
        :return:
        """
        self.prune_undo()
        self.prune_redo()

        actions.execute()                   # Execute command
        self.undo_stack.append(actions)     # Add operation to undo-stack

    # Undo the most recent operation:
    def undo(self):
        """
        Undoes the most recent action by popping it from the undo stack and executing its undo method. The action is then
        added to the redo stack for potential redoing later.
        :return:
        """
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
        """
        Redoes the most recent action by popping it from the redo stack and executing its redo method. The action is then
        added back to the undo stack for potential undoing later.
        :return:
        """
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
        """
        Prunes the undo stack by removing actions older than the maximum allowed number of undo actions (MAX_UNDO).
        :return:
        """
        # Prune actions older than MAX_UNDO turns:
        while len(self.undo_stack) > ActionsManager.MAX_UNDO:
            to_be_purged = self.undo_stack.pop(0)   # Pop the oldest command:
            to_be_purged.cleanup()                  # Delete items

    # Clears redo stack with every do-operation:
    def prune_redo(self):
        """
        Prunes the redo stack by removing all actions. This is done to ensure that once a new action is performed, the
        redo stack is cleared, preventing the user from redoing actions that are no longer relevant.
        :return:
        """
        # Clear redo stack:
        while len(self.redo_stack):
            to_be_purged = self.redo_stack.pop(0)   # Pop the oldest command
            to_be_purged.cleanup()                  # Delete items

    # Clears undo and redo stacks, deletes resources:
    def wipe_stack(self):
        """
        Wipes the undo and redo stacks by clearing all actions and deleting their resources. This is useful for resetting
        the action history in the application.
        :return:
        """
        # Safe-delete all previous actions:
        while len(self.undo_stack):
            to_be_purged = self.undo_stack.pop(0)   # Pop the oldest command:
            to_be_purged.cleanup()                  # Delete items

        self.prune_redo()