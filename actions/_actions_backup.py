import logging
import weakref

from custom.entity import EntityClass

# Abstract action:
class AbstractAction:

    def __init__(self):     self._is_obsolete = False

    def set_obsolete(self): self._is_obsolete = True

    def set_relevant(self): self._is_obsolete = False

    def execute(self)   -> None : raise NotImplementedError()

    def undo(self)      -> None : raise NotImplementedError()

    def redo(self)      -> None : raise NotImplementedError()

    def cleanup(self)   -> None : raise NotImplementedError()

# Class BatchActions: Groups actions together and executes them
class BatchActions(AbstractAction):

    def __init__(self, actions: list | None):

        # Initialize base-class:
        super().__init__()

        # Actions-sequence:
        self.actions = actions or []

    def size(self):     return len(self.actions)

    def clear(self):    self.actions.clear()

    def set_obsolete(self):

        # Call `set_obsolete` for each action:
        for action in self.actions:
            action.set_obsolete()

    def add_to_batch(self, _actions: list[AbstractAction] | AbstractAction):
        if   isinstance(_actions, list)          :  self.actions += _actions
        elif isinstance(_actions, AbstractAction):  self.actions.append(_actions)

    def cleanup(self) -> None:  [action.cleanup() for action in self.actions]

    def execute(self) -> None:  [action.execute() for action in self.actions]

    def undo(self) -> None:     [action.undo() for action in reversed(self.actions)]

    def redo(self) -> None:     [action.redo() for action in reversed(self.actions)]

    def info(self) -> str:      return f"Batch ({len(self.actions)} actions)"

# Class CreateNodeAction: For node operations (create, undo/redo)
class CreateNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, _canvas, _node):

        # Initialize super-class:
        super().__init__()

        # Store strong-references:
        self.cref = _canvas
        self.nref = _node

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.nref.destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return 
        
        if  self.nref.isEnabled():
            logging.info(f"Node is active, aborting cleanup.")
            return

        # Remove node from the database & canvas:
        self.cref.node_db.pop(self.nref, None)
        self.cref.removeItem (self.nref)

        # Delete the node's handles:
        dictionary = self.nref.get_dict(EntityClass.INP) | self.nref.get_dict(EntityClass.OUT)
        while dictionary:
            _handle = dictionary.popitem()[0]
            _handle.deleteLater()

        # Log and delete node:
        logging.info(f"Deleting Object - {self.nref.uid}")
        self.nref.deleteLater()

    def execute(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        # Add node to canvas:
        self.cref.node_db[self.nref] = True
        self.cref.addItem(self.nref)

    def undo(self)  -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.nref.isEnabled():
            logging.info(f"Node is already disabled, aborting execution.")
            return

        # Disable node, toggle visibility and block signals:
        self.cref.node_db[self.nref] = False
        self.nref.setVisible(False)             # Make node invisible
        self.nref.setEnabled(False)             # Disable node   
        self.nref.blockSignals(True)            # Block signals, this must come last

    def redo(self)  -> None:

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        if  self.nref.isEnabled():
            logging.info(f"Node is already enabled, aborting execution.")
            return
      
        # Toggle dictionary value-flag:
        self.cref.node_db[self.nref] = True
        self.nref.blockSignals(False)            # Unblock signals, this must come first    
        self.nref.setEnabled(True)               # Enable node
        self.nref.setVisible(True)               # Make node visible

    def info(self):
        
        # Abort-condition:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[CreateNodeAction] -> {self.nref.uid}"

# Class RemoveNodeAction: For node operations (delete, undo/redo)
class RemoveNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, _canvas, _node):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = _canvas
        self.nref = _node

        # Connect objects' destroyed signal:
        self.cref.destroyed.connect(self.set_obsolete)
        self.nref.destroyed.connect(self.set_obsolete)

    def cleanup(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return
        
        if  self.nref.isEnabled():
            logging.info(f"Node is active, aborting cleanup.")
            return

        # Remove node from scene's database:
        self.cref.node_db.pop(self.nref, None)
        self.cref.removeItem (self.nref)

        # Delete the node's handles:
        dictionary = self.nref.get_dict(EntityClass.INP) | self.nref.get_dict(EntityClass.OUT)
        while dictionary:
            _handle = dictionary.popitem()[0]
            _handle.deleteLater()

        # Log and delete node:
        logging.info(f"Deleting Object - {self.nref.uid}")
        self.nref.deleteLater()

    def execute(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        if  not self.nref.isEnabled():
            logging.info(f"Node is already disabled, aborting execution.")
            return

        # Remove node from scene's database:
        self.cref.node_db[self.nref] = False
        self.nref.setVisible(False)
        self.nref.setEnabled(False)
        self.nref.blockSignals(True)

    def undo(self)  -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        if  self.nref.isEnabled():
            logging.info(f"Node is already enabled, aborting execution.")
            return

        # Toggle activation flag:
        self.cref.node_db[self.nref] = True
        self.nref.blockSignals(False)
        self.nref.setEnabled(True)
        self.nref.setVisible(True)

    def redo(self)  -> None:    self.execute()

    def info(self):

        # Abort-condition:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[RemoveNodeAction] -> {self.nref.uid}"

# Class CreateStreamAction: For stream operations (create, undo/redo)
class CreateStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, _canvas, _terminal):

        # Initialize super-class:
        super().__init__()

        # Strong reference(s):
        self.cref = _canvas
        self.tref = _terminal

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.tref.destroyed.connect(self.set_obsolete)

    def cleanup(self)   -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return
        
        if  self.tref.isEnabled():
            logging.info(f"Terminal is active, aborting cleanup.")
            return

        # Remove terminal from scene's database:
        self.cref.term_db.pop(self.tref, None)
        self.cref.removeItem (self.tref)

        # Schedule deletion:
        logging.info(f"Deleting terminal {self.tref.uid}")
        self.tref.socket.free()
        self.tref.deleteLater()

    def execute(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        # Add terminal to the scene:
        self.cref.term_db[self.tref] = True
        self.cref.addItem(self.tref)

    def undo(self)  -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.tref.isEnabled():
            logging.info(f"Terminal is already disabled, aborting execution.")  
            return

        # Disable terminal, toggle visibility and block signals:
        self.cref.term_db[self.tref] = False
        self.tref.setVisible(False)
        self.tref.setEnabled(False)
        self.tref.blockSignals(True)

    def redo(self)  -> None:

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        if  self.tref.isEnabled():
            logging.info(f"Terminal is already enabled, aborting execution.")
            return

        # Re-activate terminal, toggle visibility and unblock signals:
        self.cref.term_db[self.tref] = True
        self.tref.blockSignals(False)
        self.tref.setEnabled(True)
        self.tref.setVisible(True)

    def info(self):

        # Abort-condition:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[CreateStreamAction] -> {self.tref.uid}"
    
# Class RemoveStreamAction: For stream operations (delete, undo/redo)
class RemoveStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, _canvas, _terminal):

        # Initialize super-class:
        super().__init__()

        # Strong reference(s):
        self.cref = _canvas
        self.tref = _terminal

        # Connect objects' destroyed signal:
        self.tref.destroyed.connect(self.set_obsolete)
        self.cref.destroyed.connect(self.set_obsolete)

    def cleanup(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return
        
        if  self.tref.isEnabled():
            logging.info(f"Terminal is active, aborting cleanup.")
            return

        # Remove terminal from scene's database:
        self.cref.term_db.pop(self.tref, None)
        self.cref.removeItem (self.tref)

        # Schedule terminal-deletion:
        logging.info(f"Deleting terminal {self.tref.uid}")
        self.tref.socket.free()
        self.tref.deleteLater()

    def execute(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        if  not self.tref.isEnabled():
            logging.info(f"Terminal is already disabled, aborting execution.")
            return

        # Disable terminal:
        self.cref.term_db[self.tref] = False
        self.tref.setVisible(False)
        self.tref.setEnabled(False)
        self.tref.blockSignals(True)

        # If connected, disconnect the terminal:
        if self.tref.socket.connected:
            self.tref.socket.conjugate().free()             # Free conjugate
            self.tref.socket.connector().blockSignals(True) # Block signals
            self.tref.socket.connector().setVisible(False)  # Hide connector
            self.tref.socket.connector().setEnabled(False)  # Disable connector

    def undo(self)  -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  self.tref.isEnabled():
            logging.info(f"Terminal is already enabled, aborting execution.")
            return 
    
        # Re-activate terminal:
        self.cref.term_db[self.tref] = True
        self.tref.blockSignals(False)
        self.tref.setEnabled(True)
        self.tref.setVisible(True)

        # Reconnect terminal:
        if self.tref.socket.connected:

            self.tref.socket.connector().blockSignals(False)    # Unblock signals
            self.tref.socket.connector().setVisible(True)       # Show connector
            self.tref.socket.connector().setEnabled(True)       # Enable connector
            self.tref.socket.conjugate().lock(                  # Lock the terminal's conjugate
                self.tref.socket, 
                self.tref.socket.connector()
                )

    def redo(self)  -> None:    self.execute()

    def info(self):

        # Abort-condition:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[RemoveStreamAction] -> {self.tref.uid}"
    
# Class CreateHandleAction: For handle operations (create, undo/redo)
class CreateHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, _node, _handle):

        # Initialize super-class:
        super().__init__()

        # Strong reference(s):
        self.nref = _node
        self.href = _handle

        # Connect objects' destroyed signal:
        self.nref.destroyed.connect(self.set_obsolete)
        self.href.destroyed.connect(self.set_obsolete)

    def cleanup(self)   -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return

        if  self.href.isEnabled():
            logging.info(f"Handle is active, aborting cleanup.")
            return

        # Delete handle:
        logging.info(f"Deleting handle {self.href.uid}")
        self.nref.get_dict(self.href.stream).pop(self.href, None)
        self.href.deleteLater()

        if  self.nref.scene():  self.nref.scene().removeItem(self.href)

    def execute(self) -> None:

        # Abort-condition:
        if self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return
        
        # Add handle to node and connect signals:
        self.nref.get_dict(self.href.stream)[self.href] = True

    def undo(self)  -> None:

        # Abort-condition:
        if self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.href.isEnabled():
            logging.info(f"Handle is already disabled, aborting execution.")
            return

        # Deactivate handle:
        self.nref.get_dict(self.href.stream)[self.href] = False
        self.href.setVisible(False)
        self.href.setEnabled(False)
        self.href.blockSignals(True)

    def redo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  self.href.isEnabled():
            logging.info(f"Handle is already enabled, aborting execution.")
            return

        # Reactivate handle:
        self.nref.get_dict(self.href.stream)[self.href] = True
        self.href.blockSignals(False)
        self.href.setEnabled(True)
        self.href.setVisible(True)

    def info(self):

        # Null-check:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[CreateHandleAction] -> {self.href.uid}"

# Class RemoveHandleAction: For handle operations (delete, undo/redo)
class RemoveHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, _node, _handle):

        # Initialize super-class:
        super().__init__()

        # Strong reference(s):
        self.nref = _node
        self.href = _handle

        # Connect objects' destroyed signal:
        self.nref.destroyed.connect(self.set_obsolete)
        self.href.destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return

        if  self.href.isEnabled():
            logging.info(f"Handle is active, aborting cleanup.")
            return

        # If handle is connected, delete connector:
        if  self.href.connector():  self.href.connector().delete()

        # Remove handle from node's database, and scene:
        self.nref.get_dict(self.href.stream).pop(self.href, None)
        self.href.deleteLater()

        if  self.nref.scene():  self.nref.scene().removeItem(self.href)

    def execute(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.href.isEnabled():
            logging.info(f"Handle is already disabled, aborting execution.")
            return

        # Remove the handle's connector:
        if  self.href.connector():
            self.href.conjugate().free()                # Free conjugate
            self.href.connector().blockSignals(True)    # Block signals
            self.href.connector().setVisible(False)     # Hide connector
            self.href.connector().setEnabled(False)     # Disable connector

        # Toggle activation flag:
        self.nref.get_dict(self.href.stream)[self.href] = False
        self.href.setVisible(False)
        self.href.setEnabled(False)
        self.href.blockSignals(True)

    def undo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  self.href.isEnabled():
            logging.info(f"Handle is already enabled, aborting execution.")
            return

        # Reconnect handle with its conjugate:
        if  self.href.connector():
            self.href.connector().blockSignals(False)    # Unblock signals
            self.href.connector().setVisible(True)       # Show connector
            self.href.connector().setEnabled(True)       # Enable connector
            self.href.conjugate().lock(
                self.href, 
                self.href.connector()
                )

        # Toggle activation flag:
        self.nref.get_dict(self.href.stream)[self.href] = True
        self.href.blockSignals(False)
        self.href.setVisible(True)
        self.href.setEnabled(True)

    def redo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.href.isEnabled():
            logging.info(f"Handle is already enabled, aborting execution.")
            return  

        # Remove the handle's connector:
        if  self.href.connector():

            # Free conjugate handle:
            self.href.conjugate().connected = None
            self.href.conjugate().conjugate = None
            self.href.conjugate().connector = None

            # Deactivate connector:
            self.href.connector().blockSignals(True)
            self.href.connector().setVisible(False)
            self.href.connector().setEnabled(False)

        # Toggle activation flag:
        self.nref.get_dict(self.href.stream)[self.href] = False
        self.href.setVisible(False)
        self.href.setEnabled(False)
        self.href.blockSignals(False)

    def info(self):

        # Null-check:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[RemoveHandleAction] -> {self.href.uid}"

# Class ConnectHandleAction: For connector operations (create, undo/redo)
class ConnectHandleAction(AbstractAction):

    # Initializer:  
    def __init__(self, _canvas, _connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = _canvas
        self.lref = _connector

        # Connect objects' destroyed signals:
        self.cref.destroyed.connect(self.set_obsolete)
        self.lref.destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None:

        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return
        
        if  self.lref.isEnabled():
            logging.info(f"Connector is active, aborting cleanup.")
            return

        # Remove connector from canvas and delete:
        self.cref.conn_db.pop(self.lref, None)
        self.cref.removeItem (self.lref)
        self.lref.deleteLater()

    def execute(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        # Add connector to the canvas's database, then add to scene:
        self.cref.conn_db[self.lref] = True
        self.cref.addItem(self.lref)

    def undo(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.lref.isEnabled():
            logging.info(f"Connector is already disabled, aborting execution.")
            return  

        # Remove connector from canvas and delete:
        self.cref.conn_db[self.lref] = False
        self.lref.origin.free()
        self.lref.target.free()

        # Disable connector:
        self.lref.setVisible(False)
        self.lref.setEnabled(False)
        self.lref.blockSignals(True)

    def redo(self):

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  self.lref.isEnabled():
            logging.info(f"Connector is already enabled, aborting execution.")
            return  

        # Toggle activation flag:
        self.cref.conn_db[self.lref] = True
        self.lref.origin.lock(self.lref.target, self.lref)
        self.lref.target.lock(self.lref.origin, self.lref)

        # Deactivate connector:
        self.lref.setVisible(True)
        self.lref.setEnabled(True)
        self.lref.blockSignals(False)

    def info(self):

        # Abort-condition:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[ConnectHandleAction] -> {self.lref.uid}"
    
# Class DisconnectHandleAction: For connector operations (delete, undo/redo)
class DisconnectHandleAction(AbstractAction):

    def __init__(self, _canvas, _connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = _canvas
        self.lref = _connector

        # Connect objects' destroyed signal:
        self.cref.destroyed.connect(self.set_obsolete)
        self.lref.destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting cleanup.")
            return

        if  self.lref.isEnabled():
            logging.info(f"Connector is active, aborting cleanup.")
            return

        # Remove connector from canvas:
        self.cref.conn_db.pop(self.lref, None)
        self.cref.removeItem (self.lref)
        
        # Delete connector:
        logging.info(f"Deleting connector {self.lref.uid}")
        self.lref.deleteLater()

    def execute(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  not self.lref.isEnabled():
            logging.info(f"Connector is already disabled, aborting execution.")
            return

        # Toggle activation flag:
        self.cref.conn_db[self.lref] = False
        self.lref.origin.free()
        self.lref.target.free()

        # Deactivate connector:
        self.lref.setVisible(False)
        self.lref.setEnabled(False)
        self.lref.blockSignals(True)

    def undo(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) already destroyed, aborting execution.")
            return

        if  self.lref.isEnabled():
            logging.info(f"Connector is already enabled, aborting execution.")
            return

        # Toggle activation flag:
        self.cref.conn_db[self.lref] = True
        self.lref.origin.lock(self.lref.target, self.lref)
        self.lref.target.lock(self.lref.origin, self.lref)

        # Reactivate connector:
        self.lref.setVisible(True)
        self.lref.setEnabled(True)
        self.lref.blockSignals(False)

    def redo(self)  -> None:    self.execute()

    def info(self):

        # Null-check:
        if self._is_obsolete:   return None

        # Return action-info:
        return f"[DisconnectHandleAction] -> {self.lref.uid}"