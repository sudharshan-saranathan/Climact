import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform, QColor
from PyQt6.QtWidgets import QGraphicsObject, QMessageBox

from tabs.schema import graph
from custom      import *
from actions     import *

class JsonIO:
    """
    Class for serializing and deserializing schematics (nodes and connectors)
    to and from JSON format for the canvas-based process modeling application.

    Static Methods:
    ---------------
    - serialize(item):
        Serializes a single `Node` or `Connector` object to a JSON-compatible dictionary.
        Includes _node position, size, equations, and variables; or connector endpoints.

    - encode_json(canvas):
        Serializes all selected items from the canvas (or all nodes and connectors if none are selected)3
        into a JSON string. Used for exporting schematics or dragging between scenes.

    - decode_json(code: str, canvas):
        Parses a schematic JSON string and reconstructs the corresponding nodes, variables, and connectors
        on the given `Canvas`. All actions are grouped into a single undoable `BatchAction`.
    """

    @staticmethod
    def entity_to_json(entity: Entity, eclass: EntityClass):

        # Determine prefix:
        if  eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            prefix = "variable"

        elif eclass == EntityClass.PAR:
             prefix = "parameter"

        else:
            logging.warning(f"Expected argument of type `EntityClass`, skipping JSON!")
            return None

        # Create JSON-object:
        entity_obj = {
                    f"{prefix}-eclass"   : entity.eclass.name,
                    f"{prefix}-symbol"   : entity.symbol,
                    f"{prefix}-label"    : entity.label,
                    f"{prefix}-units"    : entity.units,
                    f"{prefix}-strid"    : entity.strid,
                    f"{prefix}-info"     : entity.info,
                    f"{prefix}-value"    : entity.value,
                    f"{prefix}-sigma"    : entity.sigma,
                    f"{prefix}-minimum"  : entity.minimum,
                    f"{prefix}-maximum"  : entity.maximum,
                }
        
        # For variables, add coordinates relative to _node and canvas:
        if eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            
            entity_obj.update({
                f"{prefix}-position" : {            # Position relative to _node
                    "x": entity.pos().x(),
                    "y": entity.pos().y()
                },
                f"{prefix}-scenepos" : {            # Position relative to canvas
                    "x": entity.scenePos().x(),
                    "y": entity.scenePos().y()
                }
            })

        # Return dictionary:
        return entity_obj

    @staticmethod
    def json_to_entity(
        entity: Entity,        # Entity object to be updated.
        eclass: EntityClass,   # Entity's class
        jsdict: json,          # JSON-dictionary containing the entity's attributes.
        symbol: bool = True    # Whether to set the symbol from the JSON code
    ):

        # Determine prefix:
        if eclass in [
            EntityClass.INP,
            EntityClass.OUT,
            EntityClass.VAR]:   prefix = "variable"

        elif eclass == EntityClass.PAR:    prefix = "parameter"
        else:   raise ValueError(f"Invalid entity class: {eclass}")

        # If the flag is set, copy the symbol:
        if symbol: entity.symbol = jsdict.get(f"{prefix}-symbol")

        # Read other attribute(s):
        entity.label   = jsdict.get(f"{prefix}-label")
        entity.units   = jsdict.get(f"{prefix}-units")
        entity.info    = jsdict.get(f"{prefix}-info")
        entity.strid   = jsdict.get(f"{prefix}-strid")
        entity.value   = jsdict.get(f"{prefix}-value")
        entity.sigma   = jsdict.get(f"{prefix}-sigma")
        entity.minimum = jsdict.get(f"{prefix}-minimum")
        entity.maximum = jsdict.get(f"{prefix}-maximum")

    @staticmethod
    def serialize(item: QGraphicsObject):
        """
        Serializes a single `QGraphicsObject` to a JSON object.

        Args:
            item (QGraphicsObject): The `QGraphicsObject` to serialize.

        Returns:
            dict: A JSON-object containing the item's serialized attributes and children.
        """

        # If the instance is a _node, serialize the _node's variables, parameters, and equations:
        if isinstance(item, graph.Node):

            # Construct a list of the _node's active variables:
            variables = [
                JsonIO.entity_to_json(entity, EntityClass.VAR)
                for entity, state in item[EntityClass.VAR].items()
                if  state == EntityState.ACTIVE
            ]

            # Construct a list of the _node's active parameters:
            parameters = [
                JsonIO.entity_to_json(entity, EntityClass.PAR)
                for entity, state in item[EntityClass.PAR].items()
                if  state == EntityState.ACTIVE
            ]

            # Create a list of equations:
            equations = item[EntityClass.EQN]

            # JSON-composite:
            node_object = {
                "node-title"    : item.title,                      # Node's title
                "node-color"    : item._style.background.name(),   # Node's background color
                "node-height"   : item.boundingRect().height(),    # Node's height
                "node-scenepos" : {                                 # Node's scene-position
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                },
                "parameters"  : parameters,                         # Node's active parameters
                "variables"   : variables,                          # Node's active variables
                "equations"   : equations                           # Node's equations
            }

            # Return the _node's JSON object:
            return node_object

        # If the instance is a terminal, serialize the terminal's attributes:
        if isinstance(item, graph.StreamTerminal):

            # Create JSON-object:
            stream_obj = {
                "terminal-eclass"   : item.handle.eclass.name,
                "terminal-label"    : item.handle.label,
                "terminal-strid"    : item.handle.strid,
                "terminal-scenepos" : {
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                }
            }

            # Return the terminal's JSON object:
            return stream_obj

        # If the instance is a connector, serialize the connector's attributes:
        if  isinstance(item, graph.Connector):

            # Create JSON-object:
            connection_obj = {
                "origin-parent-uid" : item.origin.parentItem().uid,
                "origin-eclass"     : item.origin.eclass.name,
                "origin-label"      : item.origin.label,
                "origin-scenepos"   : {
                    "x": item.origin.scenePos().x(),
                    "y": item.origin.scenePos().y()
                },
                "target-parent-uid" : item.target.parentItem().uid,
                "target-eclass"     : item.target.eclass.name,
                "target-label"      : item.target.label,
                "target-scenepos": {
                    "x": item.target.scenePos().x(),
                    "y": item.target.scenePos().y()
                }
            }

            # Return the connector's JSON object:
            return connection_obj

        # If the instance is not a _node, terminal, or connector, return None:
        return None

    @staticmethod
    def encode(canvas):
        """
        Serializes all items in the canvas (nodes, terminals, and connectors) into a JSON string.
        :param canvas: The `Canvas` object containing the items to serialize.
        """

        total_items_list = (
            [item for item, state in canvas.node_db.items() if state == EntityState.ACTIVE] +     # Active nodes
            [item for item, state in canvas.term_db.items() if state == EntityState.ACTIVE] +     # Active terminals
            [item for item, state in canvas.conn_db.items() if state == EntityState.ACTIVE]       # Active connectors
        )

        # Fetch serialized JSON objects for each item-type:
        node_array = [JsonIO.serialize(item) for item in total_items_list if isinstance(item, graph.Node)]
        conn_array = [JsonIO.serialize(item) for item in total_items_list if isinstance(item, graph.Connector)]
        term_array = [JsonIO.serialize(item) for item in total_items_list if isinstance(item, graph.StreamTerminal)]

        # Initialize JSON objects:
        schematic = {
            "NODES"      : node_array,  # Add all active nodes
            "TERMINALS"  : term_array,  # Add all active terminals
            "CONNECTORS" : conn_array   # Add all active connectors
        }

        # Return JSON string:
        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode(code: str,
               canvas,
               combine: bool = False
               ):
        """
        Parses a schematic JSON string and reconstructs the corresponding nodes, variables, and connectors
        on the given `Canvas`. All actions are grouped into a single undoable `BatchAction`.

        Args:
            code (str): The JSON string to parse.
            canvas (Canvas): The canvas to reconstruct the schematic on.
            combine (bool): Whether to combine the actions into a single undoable `BatchAction`.

        Returns:
            None
        """

        # Import canvas module (required for executing canvas operations):
        from tabs.schema.canvas import Canvas

        # Create a symbol map to track how variable-symbols are changed during JSON-decoding:
        symmap = dict()

        # Initialize convenience-variables:
        mean  = list()
        root  = json.loads(code)
        batch = BatchActions([])

        # Validate argument(s):
        if not isinstance(code, str):      raise ValueError("Invalid JSON code")
        if not isinstance(canvas, Canvas): raise ValueError("Invalid `Canvas` object")

        # Read JSON and execute operations:
        # Nodes:
        for node_json in root.get("NODES") or []:

            height = node_json.get("node-height")
            color  = node_json.get("node-color") or 0xffffff
            title  = node_json.get("node-title")
            npos   = QPointF(
                node_json.get("node-scenepos").get("x"),
                node_json.get("node-scenepos").get("y")
            )
            mean.append(npos)

            new_node = canvas.create_node(
                title,  # Title
                npos,   # Coordinate
                False   # Do not create a corresponding action
            )

            new_node.resize(int(height) - 150)                    # Adjust _node's height
            new_node.on_set_color(QColor(color))                  # Set the node's color
            canvas.node_db[new_node] = EntityState.ACTIVE         # Add node to canvas' database:
            canvas.addItem(new_node)                              # Add node to canvas

            # Add action to batch:
            batch.add_to_batch(CreateNodeAction(canvas, new_node))

            # Add variable(s):
            for var_json in node_json.get("variables") or []:

                # Get variable's EntityClass:
                eclass = EntityClass.INP if (
                    var_json.get("variable-eclass") == "INP" or 
                    var_json.get("variable-eclass") == "EntityClass.INP"
                ) \
                else EntityClass.OUT

                # Get variable's coordinate:
                hpos = QPointF(
                    var_json.get("variable-position").get("x"),
                    var_json.get("variable-position").get("y")
                )

                # Instantiate new variable with given EntityClass and coordinate:
                _var = new_node.create_handle(eclass, hpos)

                # Read other attribute(s):
                JsonIO.json_to_entity(
                    _var,
                    eclass,
                    var_json,
                    False
                )

                # Update variable's color and label:
                _var.rename(_var.label)
                _var.create_stream(_var.strid)
                _var.sig_item_updated.emit(_var)    # Emit signal to notify application of changes

                # Add the variable to the node's database and modify the node's equations to use the variable's new symbol:
                new_node[eclass][_var] = EntityState.ACTIVE

                # Add action to batch:
                batch.add_to_batch(CreateHandleAction(new_node, _var))

            # Add parameter(s):
            for par_json in node_json.get("parameters") or []:

                # Instantiate new parameter:
                _par = Entity()
                _par.eclass = EntityClass.PAR

                # Read other attribute(s):
                JsonIO.json_to_entity(_par, EntityClass.PAR, par_json)

                # Add parameter to _node's database:
                new_node[EntityClass.PAR][_par] = EntityState.ACTIVE

            # Add equations(s):
            if node_json.get("equations") or []:
                new_node[EntityClass.EQN, None] = [
                    equation for equation in node_json.get("equations")
                ]

        # Terminals:
        for _term_json in root.get("TERMINALS") or []:

            # Get terminal's EntityClass and coordinate:
            eclass = EntityClass.INP if (
                _term_json.get("terminal-eclass") == "INP" or 
                _term_json.get("terminal-eclass") == "EntityClass.INP"
            ) \
            else EntityClass.OUT

            # Get terminal's coordinate:
            tpos = QPointF(
                _term_json.get("terminal-scenepos").get("x"),
                _term_json.get("terminal-scenepos").get("y")
            )

            mean.append(tpos)

            # Create terminal:
            _terminal = canvas.create_terminal(eclass, tpos)
            _terminal.handle.rename(_term_json.get("terminal-label"))
            _terminal.handle.create_stream(_term_json.get("terminal-strid"))
            _terminal.handle.sig_item_updated.emit(_terminal.handle)

            # Add terminal to the database and canvas:
            canvas.term_db[_terminal] = EntityState.ACTIVE
            canvas.addItem(_terminal)

        # Connections:
        for conn_json in root.get("CONNECTORS") or []:

            # Origin handle's scene-position:
            opos = QPointF(
                conn_json.get("origin-scenepos").get("x"),
                conn_json.get("origin-scenepos").get("y")
            )

            # Target handle's scene-position:
            tpos = QPointF(
                conn_json.get("target-scenepos").get("x"),
                conn_json.get("target-scenepos").get("y")
            )

            origin = canvas.itemAt(opos, QTransform()) # Origin-reference
            target = canvas.itemAt(tpos, QTransform()) # Target-reference

            if not isinstance(origin, graph.Handle):    continue
            if not isinstance(target, graph.Handle):    continue

            # Establish a new connection:
            try:

                # Create a new connector:
                connector = graph.Connector(canvas.create_cuid(),
                                            origin,
                                            target,
                                            False
                                            )

                # Add connector to database and canvas:
                canvas.conn_db[connector] = EntityState.ACTIVE
                canvas.addItem(connector)

                # Add connector-creation action to batch:
                batch.add_to_batch(ConnectHandleAction(canvas, connector))

            # If an exception occurs, print error:
            except Exception as exception:
                logging.exception(f"Connector creation skipped due to an exception: {exception}")

        # Execute batch:
        if combine: canvas.manager.do(batch)

        # Re-center the schematic:
        import numpy as np

        center = canvas.sceneRect().center()
        mean   = QPointF(
            sum([point.x() for point in mean]) / len(mean),
            sum([point.y() for point in mean]) / len(mean)
        )

        # Center the schematic:
        for item in canvas.node_db | canvas.term_db:
            item.moveBy(center - mean)
