import logging
from tabs.schema.graph.anchor    import StreamType

# Abstract action:
class AbstractAction:

    def __init__(self):
        self._is_obsolete = False

    def set_obsolete(self):
        self._is_obsolete = True

    def set_relevant(self):
        self._is_obsolete = False

    def execute(self)           -> None :   raise NotImplementedError()
    def undo(self)              -> None :   raise NotImplementedError()
    def redo(self)              -> None :   raise NotImplementedError()
    def cleanup(self)           -> None :   raise NotImplementedError()

# Class BatchActions: Groups actions together and executes them
class BatchActions(AbstractAction):

    # Initializer:
    def __init__(self, actions: list | None):

        # Initialize base-class:
        super().__init__()

        # Actions-sequence:
        self.actions = actions or []

    # Return batch-size:
    def size(self): return len(self.actions)

    # Add actions to the batch:
    def add_to_batch(self, action: AbstractAction)    -> None :
        self.actions.append(action)

    # Cleanup when stack is pruned:
    def cleanup(self)   -> None :
        for action in self.actions:
            action.cleanup()

    # Execute batch-actions:
    def execute(self)   -> None :
        for action in self.actions:
            action.execute()

    # Undo batch-operations:
    def undo(self)  -> None :
        for action in reversed(self.actions):
            action.undo()

    # Redo batch-operations:
    def redo(self)  -> None :
        for action in reversed(self.actions):
            action.redo()

    # Returns info about this action:
    def info(self):
        return f"Batch ({len(self.actions)} actions)"

# Class CreateNodeAction: For node operations (create, undo/redo)
class CreateNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, node):

        # Initialize base-class:
        super().__init__()

        # References:
        self.cref = canvas
        self.nref = node

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.nref.destroyed.connect(self.set_obsolete)

    # Triggered by stack-manager's prune functions:
    def cleanup(self)   -> None :

        # If obsolete, log and return:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.cleanup(): Action obsolete!")
            return

        # Trigger deletion of unused nodes:
        if  not self.nref.isEnabled():

            # Remove node from scene's database:
            if  self.nref in self.cref.node_items.keys():
                self.cref.node_items.pop(self.nref)

            # Remove node from scene:
            if  self.nref.scene() == self.cref:
                self.cref.removeItem(self.nref)

            # Delete the node's handles:
            while len(self.nref[StreamType.INP]):
                handle = self.nref[StreamType.INP].popitem()[0]
                handle.deleteLater()

            # Delete the node's handles:
            while len(self.nref[StreamType.OUT]):
                handle = self.nref[StreamType.OUT].popitem()[0]
                handle.deleteLater()

            # Schedule node-deletion:
            logging.info(f"CreateNodeAction.cleanup(): Scheduling {self.nref.uid} for deletion")
            self.nref.deleteLater()

    # Execute action:
    def execute(self)   -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.execute(): Action obsolete!")
            return

        # Add node to the scene:
        if  self.nref.scene() is None:
            self.cref.node_items[self.nref] = True
            self.cref.addItem(self.nref)

    # Undo operation:
    def undo(self)  -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.undo(): Action obsolete!")
            return

        # Disable node:
        if  self.nref.isEnabled():

            # Toggle dictionary value-flag:
            if self.nref in self.cref.node_items.keys():
                self.cref.node_items[self.nref] = False

            # Deactivate node:
            self.nref.setVisible(False)
            self.nref.setEnabled(False)
            self.nref.blockSignals(True)

    # Redo operation:
    def redo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.redo(): Action obsolete!")
            return

        # Re-activate node and toggle visibility:
        if  not self.nref.isEnabled():

            # Toggle dictionary value-flag:
            if self.nref in self.cref.node_items.keys():
                self.cref.node_items[self.nref] = True

            # Activate node:
            self.nref.blockSignals(False)
            self.nref.setEnabled(True)
            self.nref.setVisible(True)

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[CreateNodeAction] -> {self.nref.uid}"
        return message

# Class RemoveNodeAction: For node operations (delete, undo/redo)
class RemoveNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, node):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = canvas
        self.nref = node

        # Connect objects' destroyed signal:
        self.cref.destroyed.connect(self.set_obsolete)
        self.nref.destroyed.connect(self.set_obsolete)

    # Cleanup when the stack is pruned:
    def cleanup(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveNodeAction.cleanup(): Action obsolete!")
            return

        # Trigger deletion of unused nodes:
        if  not self.nref.isEnabled():

            # Remove node from scene's database:
            if  self.nref in self.cref.node_items.keys():
                self.cref.node_items.pop(self.nref)

            # Remove node from scene:
            if  self.nref.scene() == self.cref:
                self.cref.removeItem(self.nref)

            # Delete the node's handles:
            while len(self.nref[StreamType.INP]):
                handle = self.nref[StreamType.INP].popitem()[0]
                handle.deleteLater()

            # Delete the node's handles:
            while len(self.nref[StreamType.OUT]):
                handle = self.nref[StreamType.OUT].popitem()[0]
                handle.deleteLater()

            # Schedule node-deletion:
            logging.info(f"RemoveNodeAction.cleanup(): Scheduling {self.nref.uid} for deletion")
            self.nref.deleteLater()

    # Execute action:
    def execute(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveNodeAction.execute(): Action obsolete!")
            return

        # Remove n
        if  self.nref.isEnabled():

            # Toggle activation-flag:
            if self.nref in self.cref.node_items.keys():
                self.cref.node_items[self.nref] = False

            # Deactivate node:
            self.nref.setVisible(False)
            self.nref.setEnabled(False)
            self.nref.blockSignals(True)

    # Undo operation:
    def undo(self)  -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveNodeAction.undo(): Action obsolete!")
            return

        # Re-activate node:
        if  not self.nref.isEnabled():

            # Toggle activation flag:
            if self.nref in self.cref.node_items.keys():
                self.cref.node_items[self.nref] = True

            # Activate node:
            self.nref.blockSignals(False)
            self.nref.setEnabled(True)
            self.nref.setVisible(True)

    # Redo operation:
    def redo(self)  -> None:    self.execute()

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[RemoveNodeAction] -> {self.nref.uid}"
        return message

# Class CreateStreamAction: For stream operations (create, undo/redo)
class CreateStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, stream):

        # Initialize base-class:
        super().__init__()

        # References:
        self.cref = canvas
        self.sref = stream

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.sref.destroyed.connect(self.set_obsolete)

    # Triggered by stack-manager's prune functions:
    def cleanup(self)   -> None :

        # If obsolete, log and return:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.cleanup(): Action obsolete!")
            return

        # Trigger deletion of unused nodes:
        if  not self.sref.isEnabled():

            # Remove node from scene's database:
            if  self.sref in self.cref.flow_items.keys():
                self.cref.flow_items.pop(self.sref)

            # Remove stream from scene:
            if  self.sref.scene() == self.cref:
                self.cref.removeItem(self.sref)

            # Schedule deletion:
            logging.info(f"CreateStreamAction.cleanup(): Scheduling {self.sref.uid} for deletion")
            self.sref.free()
            self.sref.deleteLater()

    # Execute action:
    def execute(self)   -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateStreamAction.execute(): Action obsolete!")
            return

        # Add stream to the scene:
        if self.sref.scene() is None:
            self.cref.flow_items[self.sref] = True
            self.cref.addItem(self.sref)

    # Undo operation:
    def undo(self)  -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateStreamAction.undo(): Action obsolete!")
            return

        # Disable node:
        if  self.sref.isEnabled():

            # Toggle dictionary value-flag:
            if self.sref in self.cref.flow_items.keys():
                self.cref.node_items[self.sref] = False

            # Deactivate node:
            self.sref.setVisible(False)
            self.sref.setEnabled(False)
            self.sref.blockSignals(True)

    # Redo operation:
    def redo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateNodeAction.redo(): Action obsolete!")
            return

        # Re-activate node and toggle visibility:
        if  not self.sref.isEnabled():

            # Toggle dictionary value-flag:
            if self.sref in self.cref.flow_items.keys():
                self.cref.flow_items[self.sref] = True

            # Activate node:
            self.sref.blockSignals(False)
            self.sref.setEnabled(True)
            self.sref.setVisible(True)

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[CreateNodeAction] -> {self.sref.uid}"
        return message

# Class RemoveStreamAction: For stream operations (delete, undo/redo)
class RemoveStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, stream):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = canvas
        self.sref = stream

        # Connect objects' destroyed signal:
        self.cref.destroyed.connect(self.set_obsolete)
        self.sref.destroyed.connect(self.set_obsolete)

    # Cleanup when the stack is pruned:
    def cleanup(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveStreamAction.cleanup(): Action obsolete!")
            return

        # Trigger deletion of unused nodes:
        if  not self.sref.isEnabled():

            # Remove node from scene's database:
            if self.sref in self.cref.flow_items.keys():
                self.cref.flow_items.pop(self.sref)

            # Remove node from scene:
            if  self.sref.scene() == self.cref:
                self.cref.removeItem(self.sref)

            # Schedule node-deletion:
            logging.info(f"RemoveStreamAction.cleanup(): Scheduling {self.sref.uid} for deletion")
            self.sref.free()
            self.sref.deleteLater()

    # Execute action:
    def execute(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveStreamAction.execute(): Action obsolete!")
            return

        # Disable node:
        if  self.sref.isEnabled():

            # Toggle activation-flag:
            if  self.sref in self.cref.flow_items.keys():
                self.cref.flow_items[self.sref] = False

            # If connected, disconnect stream:
            if self.sref.socket.connected:

                # Free stream's conjugate:
                self.sref.socket.conjugate().free()

                # Deactivate connector:
                self.sref.socket.connector().blockSignals(True)
                self.sref.socket.connector().setVisible(False)
                self.sref.socket.connector().setEnabled(False)

            # Deactivate node:
            self.sref.setVisible(False)
            self.sref.setEnabled(False)
            self.sref.blockSignals(True)

            logging.info(f"Stream disabled")

    # Undo operation:
    def undo(self)  -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"RemoveStreamAction.undo(): Action obsolete!")
            return

        # Re-activate node:
        if  not self.sref.isEnabled():

            # Toggle activation flag:
            if self.sref in self.cref.flow_items.keys():
                self.cref.flow_items[self.sref] = True

            # Reconnect handle with its conjugate:
            if self.sref.socket.connected:

                # Reconnect to handle's conjugate:
                self.sref.socket.conjugate().lock(self.sref.socket, self.sref.socket.connector())

                # Re-enable connector:
                self.sref.socket.connector().blockSignals(False)
                self.sref.socket.connector().setVisible(True)
                self.sref.socket.connector().setEnabled(True)

            # Activate node:
            self.sref.blockSignals(False)
            self.sref.setEnabled(True)
            self.sref.setVisible(True)

    # Redo operation:
    def redo(self)  -> None:    self.execute()

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[RemoveStreamAction] -> {self.sref.uid}"
        return message

# Class CreateHandleAction: For handle operations (create, undo/redo)
class CreateHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, node, handle):

        # Initialize base-class:
        super().__init__()

        # Weak reference(s):
        self.nref = node
        self.href = handle

        # Connect objects' destroyed signal:
        self.nref.destroyed.connect(self.set_obsolete)
        self.href.destroyed.connect(self.set_obsolete)

    # Cleanup operation
    def cleanup(self)   -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateHandleAction.cleanup(): Action obsolete!")
            return

        # Delete handle if it is disabled:
        if  not self.href.isEnabled():

            # Remove handle from node's database:
            if  self.href in self.nref[self.href.stream]:
                self.nref[self.href.stream].pop(self.href, f"CreateHandleAction.cleanup(): {self.href.uid} not found in dictionary")

            if  self.nref.scene():
                self.nref.scene().removeItem(self.href)

            # Schedule deletion:
            logging.info(f"CreateHandleAction.cleanup(): Scheduling {self.href.uid} for deletion")
            self.href.deleteLater()

    # Execute operation:
    def execute(self)   -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateHandleAction.execute(): Action obsolete!")
            return

        # Add handle to node and connect signals:
        self.nref[self.href.stream][self.href] = True

    # Undo operation:
    def undo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateHandleAction.undo(): Action obsolete!")
            return

        # Deactivate handle:
        if  self.href.isEnabled():

            # Toggle activation-flag:
            if self.href in self.nref[self.href.stream]:
                self.nref[self.href.stream][self.href] = False

            # Deactivate handle:
            self.href.setVisible(False)
            self.href.setEnabled(False)
            self.href.blockSignals(True)

    # Redo operation:
    def redo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"CreateHandleAction.redo(): Action obsolete!")
            return

        # Deactivate handle:
        if  not self.href.isEnabled():

            # Toggle activation-flag:
            if self.href in self.nref[self.href.stream]:
                self.nref[self.href.stream][self.href] = True

            # Deactivate handle:
            self.href.blockSignals(False)
            self.href.setEnabled(True)
            self.href.setVisible(True)

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[CreateHandleAction] -> {self.href.uid}"
        return message

# Class RemoveHandleAction: For handle operations (delete, undo/redo)
class RemoveHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, node, handle):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.nref = node
        self.href = handle

        # Connect objects' destroyed signal:
        self.nref.destroyed.connect(self.set_obsolete)
        self.href.destroyed.connect(self.set_obsolete)

    # Cleanup operation:
    def cleanup(self)   -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"RemoveHandleAction.cleanup(): Action obsolete!")
            return

        # Delete handle:
        if  not self.href.isEnabled():

            # If handle is connected:
            if  self.href.connected:
                self.href.connector().delete()

            self.nref[self.href.stream].pop(self.href, f"RemoveHandleAction.cleanup(): {self.href.uid} not found in dictionary")
            if  self.nref.scene():
                self.nref.scene().removeItem(self.href)

            self.href.deleteLater()

    # Execute operation:å
    def execute(self)   -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"RemoveHandleAction.execute(): Action obsolete!")
            return

        # Remove the handle's connector:
        if self.href.connected:

            # Free this handle's conjugate:
            self.href.conjugate().free()

            # Deactivate connector:
            self.href.connector().blockSignals(True)
            self.href.connector().setVisible(False)
            self.href.connector().setEnabled(False)


        # Toggle activation flag:
        if  self.href in self.nref[self.href.stream]:
            self.nref[self.href.stream][self.href] = False

        # Deactivate handle:
        self.href.setVisible(False)
        self.href.setEnabled(False)
        self.href.blockSignals(True)

    # Undo operation:
    def undo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"RemoveHandleAction.undo(): Action obsolete!")
            return

        # Reconnect handle with its conjugate:
        if self.href.connected:

            # Reconnect to handle's conjugate:
            self.href.conjugate().lock(self.href, self.href.connector())

            # Re-enable connector:
            self.href.connector().blockSignals(False)
            self.href.connector().setVisible(True)
            self.href.connector().setEnabled(True)

        # Toggle activation flag:
        if self.href in self.nref[self.href.stream]:
            self.nref[self.href.stream][self.href] = True

        # Reactivate handle:
        self.href.blockSignals(False)
        self.href.setVisible(True)
        self.href.setEnabled(True)

    # Redo operation:
    def redo(self)  -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"RemoveHandleAction.redo(): Action obsolete!")
            return

        # Remove the handle's connector:
        if  self.href.connected:

            # Free conjugate handle:
            self.href.conjugate().connected = None
            self.href.conjugate().conjugate = None
            self.href.conjugate().connector = None

            # Deactivate connector:
            self.href.connector().blockSignals(True)
            self.href.connector().setVisible(False)
            self.href.connector().setEnabled(False)

        # Toggle activation flag:
        if self.href in self.nref[self.href.stream]:
            self.nref[self.href.stream][self.href] = False

        # Deactivate handle:
        self.href.setVisible(False)
        self.href.setEnabled(False)
        self.href.blockSignals(False)

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[RemoveHandleAction] -> {self.href.uid}"
        return message

# Class ConnectHandleAction: For connector operations (create, undo/redo)
class ConnectHandleAction(AbstractAction):

    def __init__(self, canvas, connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = canvas
        self.lref = connector

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.lref.destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None:

        if self._is_obsolete:
            logging.info(f"ConnectHandleAction.cleanup(): Action obsolete!")
            return

        if  not self.lref.isEnabled():

            # Remove connector from scene's database:
            self.cref.edge_items.pop(self.lref, f"ConnectHandleAction.cleanup(): {self.lref.uid} not found in dictionary")

            # Remove connector from scene:
            if self.lref.scene() == self.cref:
                self.cref.removeItem(self.lref)

            # Schedule deletion:
            logging.info(f"ConnectHandleAction.cleanup(): {self.lref.uid} schedule for deletion")
            self.lref.delete()

    def execute(self):

        # Null-check:
        if self._is_obsolete:
            logging.info(f"ConnectHandleAction.execute(): Action obsolete!")
            return

        # Add connector to scene:
        self.cref.edge_items[self.lref] = True
        self.cref.addItem(self.lref)

    def undo(self):

        # Null-check:
        if self._is_obsolete:
            logging.info(f"ConnectHandleAction.execute(): Action obsolete!")
            return

        # Toggle activation flag:
        if self.lref in self.cref.edge_items.keys():
            self.cref.edge_items[self.lref] = False

        # Free handles:
        self.lref.origin.free()
        self.lref.target.free()

        # Deactivate connector:
        self.lref.setVisible(False)
        self.lref.setEnabled(False)
        self.lref.blockSignals(True)

    def redo(self):

        # Null-check:
        if self._is_obsolete:
            logging.info(f"ConnectHandleAction.execute(): Action obsolete!")
            return

        # Toggle activation flag:
        if self.lref in self.cref.edge_items.keys():
            self.cref.edge_items[self.lref] = False

        # Lock handles:
        self.lref.origin.lock(self.lref.target, self.lref)
        self.lref.target.lock(self.lref.origin, self.lref)

        # Deactivate connector:
        self.lref.setVisible(True)
        self.lref.setEnabled(True)
        self.lref.blockSignals(False)

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[ConnectHandleAction] -> {self.lref.uid}"
        return message

# Class DisconnectHandleAction: For connector operations (delete, undo/redo)
class DisconnectHandleAction(AbstractAction):

    def __init__(self, canvas, connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = canvas
        self.lref = connector

        # Connect objects' destroyed signal:
        self.cref.destroyed.connect(self.set_obsolete)
        self.lref.destroyed.connect(self.set_obsolete)

    def cleanup(self)   -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"DisconnectHandleAction.cleanup(): Action obsolete!")
            return

        if  not self.lref.isEnabled():

            # Remove connector from scene:
            self.cref.edge_items.pop(self.lref, None)
            self.cref.removeItem(self.lref)

            # Schedule for deletion:
            logging.info(f"DisconnectHandleAction.cleanup(): {self.lref.uid} scheduled for deletion")
            self.lref.delete()

    def execute(self)   -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"DisconnectHandleAction.execute(): Action obsolete!")
            return

        if  self.lref.isEnabled():

            # Toggle activation flag:
            if self.lref in self.cref.edge_items.keys():
                self.cref.edge_items[self.lref] = False

            # Free origin and target handles:
            self.lref.origin.free()
            self.lref.target.free()

            # Deactivate connector:
            self.lref.setVisible(False)
            self.lref.setEnabled(False)
            self.lref.blockSignals(True)

    def undo(self) -> None:

        # Null-check:
        if self._is_obsolete:
            logging.info(f"DisconnectHandleAction.undo(): Action obsolete!")
            return

        if  not self.lref.isEnabled():

            # Toggle activation flag:
            if self.lref in self.cref.edge_items.keys():
                self.cref.edge_items[self.lref] = True

            # Free origin and target handles:
            self.lref.origin.lock(self.lref.target, self)
            self.lref.target.lock(self.lref.origin, self)

            # Deactivate connector:
            self.lref.setVisible(True)
            self.lref.setEnabled(True)
            self.lref.blockSignals(False)

    def redo(self)  -> None:    self.execute()

    # Returns info about this action:
    def info(self):

        # Null-check:
        if self._is_obsolete:
            return None

        message = f"[DisconnectHandleAction] -> {self.lref.uid}"
        return message



