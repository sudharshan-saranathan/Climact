import weakref
import logging

from custom.entity import EntityClass, EntityState


# Abstract action:
class AbstractAction:

    def __init__(self): self._is_obsolete = False

    def is_obsolete(self): return self._is_obsolete

    def set_obsolete(self): self._is_obsolete = True

    def set_relevant(self): self._is_obsolete = False

    def execute(self)   : raise NotImplementedError()

    def undo(self)      : raise NotImplementedError()

    def redo(self)      : raise NotImplementedError()

    def cleanup(self)   : raise NotImplementedError()

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

    # Re-implement `set_obsolete`:
    def set_obsolete(self):

        # Call `set_obsolete` for each action:
        for action in self.actions:
            action.set_obsolete()

    # Add actions to the batch:
    def add_to_batch(self, actions: AbstractAction | list)    -> None :

        if   isinstance(actions, list):             self.actions += actions
        elif isinstance(actions, AbstractAction):   self.actions.append(actions)

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

# Class CreateNodeAction: For _node operations (create, undo/redo)
class CreateNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, node):

        # Initialize base-class:
        super().__init__()

        # References:
        self.cref = weakref.ref(canvas)
        self.nref = weakref.ref(node)

        # Connect objects' destroyed signals:
        self.cref().destroyed.connect(self.set_obsolete)
        self.nref().destroyed.connect(self.set_obsolete)

    # Triggered by stack-manager's prune functions:
    def cleanup(self):

        # If obsolete, log and return:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, aborting cleanup!")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # If _node exists in canvas' database and is not active, remove it:
        if (
            nref in cref.node_db.keys() and
            not cref.node_db[nref]
        ):
            cref.node_db.pop(nref, None)    # Remove _node from canvas' database
            nref.deleteLater()              # Delete _node

            # Log:
            logging.info(f"Node {nref.uid} deleted")

    # Execute action:
    def execute(self): pass

    # Undo operation:
    def undo(self):

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # Deactivate _node:
        cref.node_db[nref] = False      # Mark _node as deactivated (i.e. False) in the canvas' database
        nref.setVisible(False)          # Toggle-off visibility
        nref.blockSignals(True)         # Block signals

    # Redo operation:
    def redo(self)  -> None:

        # Abort-conditions:
        if self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # Re-activate _node:
        cref.node_db[nref] = True       # Mark _node as reactivated (i.e. False) in the canvas' database
        nref.blockSignals(False)        # Toggle-on visibility
        nref.setVisible(True)           # Unblock signals

# Class RemoveNodeAction: For _node operations (delete, undo/redo)
class RemoveNodeAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, node):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = weakref.ref(canvas)
        self.nref = weakref.ref(node)

        # Connect objects' destroyed signal:
        self.cref().destroyed.connect(self.set_obsolete)
        self.nref().destroyed.connect(self.set_obsolete)

    # Cleanup when the stack is pruned:
    def cleanup(self)   -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"References destroyed, this action is obsolete")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # If _node exists in canvas' database and is not active, remove it:
        if (
            nref in cref.node_db.keys() and
            not cref.node_db[nref]
        ):

            # Delete the _node's handles (and connections):
            for _eclass in [EntityClass.INP, EntityClass.OUT]:
                while nref[_eclass]:
                    handle, state = nref[_eclass].popitem()
                    if (
                        handle.connected and
                        handle.connector()
                    ):
                        handle.connector().deleteLater()

            # Remove _node from canvas, then delete it:
            cref.node_db.pop(nref, None)
            nref.deleteLater()

            # Log:
            logging.info(f"Node {nref.uid} deleted")

    # Execute action:
    def execute(self)   -> None :

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute do-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # Note: The for-loop below removes connectors from the canvas' database. This is necessary to ensure 
        #       that the symbols for new connections are contiguous.

        for handle in nref[EntityClass.INP] | nref[EntityClass.OUT]:

            # For all connected handles
            if (
                handle.connected and 
                handle.connector()
            ):
                handle.conjugate().free()                   # Free the handle's conjugate
                handle.connector().setVisible(False)        # Toggle-off connector's visibility
                cref.conn_db[handle.connector()] = False    # Mark connector as deactivated in the canvas' database

        # Deactivate _node:
        cref.node_db[nref] = False      # Mark _node as deactivated in the canvas' database
        nref.setVisible(False)          # Toggle-off visibility
        nref.blockSignals(True)         # Block signals

    # Undo operation:
    def undo(self)  -> None :

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        nref = self.nref()  # Dereference _node pointer

        # Add connectors back to the canvas' database:
        for handle in nref[EntityClass.INP] | nref[EntityClass.OUT]:

            # For all connected handles:
            if (
                handle.connected and 
                handle.connector()
            ):
                handle.conjugate().lock(handle, handle.connector()) # Lock the handle's conjugate
                handle.connector().setVisible(True)                 # Toggle-on connector's visibility  
                cref.conn_db[handle.connector()] = True             # Mark connector as reactivated in the canvas' database

        # Reactivate _node:
        cref.node_db[nref] = True
        nref.blockSignals(False)
        nref.setVisible(True)

    # Redo operation:
    def redo(self)  -> None:    self.execute()

# Class CreateStreamAction: For stream operations (create, undo/redo)
class CreateStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, terminal):

        # Initialize base-class:
        super().__init__()

        # References:
        self.cref = weakref.ref(canvas)
        self.tref = weakref.ref(terminal)

        # Connect objects' destroyed signals:
        self.cref().destroyed.connect(self.set_obsolete)
        self.tref().destroyed.connect(self.set_obsolete)

    # Triggered by stack-manager's prune functions:
    def cleanup(self):

        # If obsolete, log and return:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        cref = self.cref()
        tref = self.tref()

        # If terminal exists in canvas' database and is not active, remove it:
        if (
            tref in cref.term_db.keys() and
            not cref.term_db[tref]
        ):
            cref.term_db.pop(tref, None)    # Remove terminal from canvas' database
            tref.deleteLater()              # Delete terminal

            # Log:
            logging.info(f"Terminal {tref.uid} deleted")


    # Execute action:
    def execute(self): pass

    # Undo operation:
    def undo(self):

        # Abort-condition:
        if self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return
        
        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # If terminal is connected, disconnect:
        if (
            tref.socket.connected and
            tref.socket.conjugate() and 
            tref.socket.connector()
        ):
            tref.socket.conjugate().free()
            tref.socket.connector().setVisible(False)
            tref.socket.connector().blockSignals(True)

        # Deactivate terminal:
        cref.term_db[tref] = False
        tref.setVisible(False)
        tref.blockSignals(True)

    # Redo operation:
    def redo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return
        
        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # If terminal is connected, disconnect:
        if (
            tref.socket.connected and
            tref.socket.conjugate() and 
            tref.socket.connector()
        ):
            tref.socket.conjugate().lock(tref.socket, tref.socket.connector())
            tref.socket.connector().blockSignals(False)
            tref.socket.connector().setVisible(True)

        # Reactivate terminal:
        cref.term_db[tref] = True
        tref.blockSignals(False)
        tref.setVisible(True)

# Class RemoveStreamAction: For stream operations (delete, undo/redo)
class RemoveStreamAction(AbstractAction):

    # Initializer:
    def __init__(self, canvas, terminal):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = weakref.ref(canvas)
        self.tref = weakref.ref(terminal)

        # Connect objects' destroyed signal:
        self.cref().destroyed.connect(self.set_obsolete)
        self.tref().destroyed.connect(self.set_obsolete)

    # Cleanup when the stack is pruned:
    def cleanup(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # If terminal exists in canvas' database and is not active, remove it:
        if (
            tref in cref.term_db.keys() and
            not cref.term_db[tref]
        ):
            cref.term_db.pop(tref, None)    # Remove terminal from canvas' database
            tref.deleteLater()              # Delete terminal

            # Log:
            logging.info(f"Terminal {tref.uid} deleted")

    # Execute action:
    def execute(self)   -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute do-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # If terminal is connected, disconnect:
        if (
            tref.socket.connected and
            tref.socket.conjugate() and 
            tref.socket.connector()
        ):
            tref.socket.conjugate().free()
            tref.socket.connector().setVisible(False)
            tref.socket.connector().blockSignals(True)

        # Deactivate terminal:
        cref.term_db[tref] = False
        tref.setVisible(False)
        tref.blockSignals(True)

    # Undo operation:
    def undo(self)  -> None :

        # Null-check:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # Reconnect terminal with its conjugate:
        if (
            tref.socket.connected and
            tref.socket.conjugate() and 
            tref.socket.connector()
        ):
            tref.socket.conjugate().lock(tref.socket, tref.socket.connector())
            tref.socket.connector().blockSignals(False)
            tref.socket.connector().setVisible(True)

        # Reactivate terminal:
        cref.term_db[tref] = True
        tref.blockSignals(False)
        tref.setVisible(True)

    # Redo operation:
    def redo(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        tref = self.tref()  # Dereference terminal pointer

        # Reconnect terminal with its conjugate:
        if (
            tref.socket.connected and
            tref.socket.conjugate() and 
            tref.socket.connector()
        ):
            tref.socket.conjugate().free()
            tref.socket.connector().setVisible(False)
            tref.socket.connector().blockSignals(True)

        # Deactivate terminal:
        cref.term_db[tref] = False
        tref.setVisible(False)
        tref.blockSignals(True)

# Class CreateHandleAction: For handle operations (create, undo/redo)
class CreateHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, node, handle):

        # Initialize base-class:
        super().__init__()

        # Weak reference(s):
        self.nref = weakref.ref(node)
        self.href = weakref.ref(handle)

        # Connect objects' destroyed signal:
        self.nref().destroyed.connect(self.set_obsolete)
        self.href().destroyed.connect(self.set_obsolete)

    # Cleanup operation
    def cleanup(self)   -> None :

        # Null-check:
        if self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        nref = self.nref()  # Dereference _node pointer
        href = self.href()  # Dereference handle pointer

        # If handle exists in _node's database, remove it:
        if (
            href in nref[href.eclass].keys() and
            nref[href.eclass][href] == EntityState.HIDDEN
        ):
            nref[href.eclass].pop(href, None)   # Remove handle from _node's database
            href.deleteLater()

            # Log:
            logging.info(f"Handle {href.uid} deleted")

    # Execute operation:
    def execute(self): pass

    # Undo operation:
    def undo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"References destroyed, cannot execute undo-action")
            return

        nref = self.nref()  # Dereference _node pointer
        href = self.href()  # Dereference handle pointer

        # Deactivate handle:
        href.setVisible(False)
        href.blockSignals(True)
        nref[href.eclass][href] = EntityState.HIDDEN

    # Redo operation:
    def redo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return

        nref = self.nref()  # Dereference _node pointer
        href = self.href()  # Dereference handle pointer

        # Reactivate handle:
        href.blockSignals(False)
        href.setVisible(True)
        nref[href.eclass][href] = EntityState.ACTIVE

# Class RemoveHandleAction: For handle operations (delete, undo/redo)
class RemoveHandleAction(AbstractAction):

    # Initializer:
    def __init__(self, node, handle):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.nref = weakref.ref(node)
        self.href = weakref.ref(handle)

        # Connect objects' destroyed signal:
        self.nref().destroyed.connect(self.set_obsolete)
        self.href().destroyed.connect(self.set_obsolete)

    # Cleanup operation:
    def cleanup(self)   -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        nref = self.nref()  # Dereference _node pointer
        href = self.href()  # Dereference handle pointer

        # If handle exists in _node's database, remove it:
        if (
            href in nref[href.eclass].keys() and
            nref[href.eclass][href] != EntityState.ACTIVE
        ):
            nref[href.eclass].pop(href, None)   # Remove handle from _node's database
            href.free(delete_connector = True)  # Delete handle's connector
            href.deleteLater()                  # Delete handle

            # Log:
            logging.info(f"Handle {href.uid} deleted")

    # Execute operation:å
    def execute(self):

        # Abort-conditions:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute do-action")
            return

        nref = self.nref()  # Dereference _node pointer
        href = self.href()  # Dereference handle pointer

        # Free the handle's conjugate
        if (
            href.connected and
            href.conjugate() and 
            href.connector()
        ):
            href.conjugate().free()
            href.connector().setVisible(False)

        # Deactivate handle:
        href.setVisible(False)
        href.blockSignals(True)

        # Deactivate handle:
        nref[href.eclass][href] = EntityState.HIDDEN

    # Undo operation:
    def undo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        nref = self.nref()
        href = self.href()

        # Reconnect handle with its conjugate:
        if (
            href.connected and
            href.conjugate() and
            href.connector()
        ):
            href.conjugate().lock(href, href.connector())
            href.connector().blockSignals(False)
            href.connector().setVisible(True)

        href.blockSignals(False)
        href.setVisible(True)
        nref[href.eclass][href] = EntityState.ACTIVE

    # Redo operation:
    def redo(self)  -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return

        nref = self.nref()
        href = self.href()

        # Remove the handle's connector:
        if (
            href.connected and
            href.conjugate() and
            href.connector()
        ):
            href.conjugate().free()
            href.connector().setVisible(False)
            href.connector().blockSignals(True)

        # Deactivate handle:
        href.setVisible(False)
        href.blockSignals(True)
        nref[href.eclass][href] = EntityState.HIDDEN

# Class ConnectHandleAction: For connector operations (create, undo/redo)
class ConnectHandleAction(AbstractAction):

    def __init__(self, canvas, connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = weakref.ref(canvas)
        self.lref = weakref.ref(connector)

        # Connect objects' destroyed signals:
        self.cref().destroyed.connect(self.set_obsolete)
        self.lref().destroyed.connect(self.set_obsolete)

    def cleanup(self) -> None:

        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # If connector exists in canvas' database and is not active, remove it:
        if (
            lref in cref.conn_db.keys() and
            not cref.conn_db[lref]
        ):
            cref.conn_db.pop(lref, None)    # Remove connector from canvas' database
            lref.deleteLater()              # Delete connector

            # Log:
            logging.info(f"Connector {lref.uid} deleted")

    def execute(self):  pass

    def undo(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # Free handles:
        lref.origin.free()
        lref.target.free()

        # Deactivate connector:
        lref.setVisible(False)
        lref.blockSignals(True)
        cref.conn_db[lref] = False

    def redo(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute redo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # Lock handles:
        lref.origin.lock(lref.target, lref)
        lref.target.lock(lref.origin, lref)

        # Deactivate connector:
        lref.setVisible(True)
        lref.blockSignals(False)
        cref.conn_db[lref] = True

# Class DisconnectHandleAction: For connector operations (delete, undo/redo)
class DisconnectHandleAction(AbstractAction):

    def __init__(self, canvas, connector):

        # Initialize base-class:
        super().__init__()

        # Strong reference(s):
        self.cref = weakref.ref(canvas)
        self.lref = weakref.ref(connector)

        # Connect objects' destroyed signal:
        self.cref().destroyed.connect(self.set_obsolete)
        self.lref().destroyed.connect(self.set_obsolete)

    def cleanup(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, this action is obsolete")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # If connector exists in canvas' database and is not active, remove it:
        if (
            lref in cref.conn_db.keys() and
            not cref.conn_db[lref]
        ):
            cref.conn_db.pop(lref, None)    # Remove connector from canvas' database
            lref.deleteLater()              # Delete connector

            # Log:
            logging.info(f"Connector {lref.uid} deleted")

    def execute(self):

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute do-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # Free handles:
        lref.origin.free()
        lref.target.free()

        # Deactivate connector:
        cref.conn_db.pop(lref, None)
        lref.setVisible(False)
        lref.blockSignals(True)

    def undo(self) -> None:

        # Abort-condition:
        if  self._is_obsolete:
            logging.info(f"Reference(s) destroyed, cannot execute undo-action")
            return

        cref = self.cref()  # Dereference canvas pointer
        lref = self.lref()  # Dereference connector pointer

        # Lock handles:
        lref.origin.lock(lref.target, lref)
        lref.target.lock(lref.origin, lref)

        # Reactivate connector:
        lref.setVisible(True)
        lref.blockSignals(False)
        cref.conn_db[lref] = True

    def redo(self): self.execute()