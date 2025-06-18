"""
jsonio.py
"""

import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform
from PyQt6.QtWidgets import QGraphicsItem

from actions import BatchActions, CreateNodeAction, CreateHandleAction, CreateStreamAction, ConnectHandleAction
from custom.entity import *
from tabs.schema.graph.handle    import Handle
from tabs.schema.graph.node      import Node
from tabs.schema.graph.terminal  import StreamTerminal
from tabs.schema.graph.connector import Connector

# Class JsonIO:
class JsonIO:
    """
    A class for reading and writing JSON-formatted schematics.
    """
    @staticmethod
    def entity_to_json(entity):
        """
        Serializes an `Entity` instance to a JSON string.
        """
        # Define prefix:
        if   entity.eclass == EntityClass.VAR:  prefix = 'variable'
        elif entity.eclass == EntityClass.PAR:  prefix = 'parameter'
        else: raise ValueError(f"Unsupported entity class: {entity.eclass}")

        entity_as_json = {
            f"{prefix}-symbol" : entity.symbol,
            f"{prefix}-eclass" : entity.eclass.name,
            f"{prefix}-strid"  : entity.strid,
            f"{prefix}-label"  : entity.label,
            f"{prefix}-units"  : entity.units,
            f"{prefix}-info"   : entity.info,
            f"{prefix}-value"  : entity.value,
            f"{prefix}-sigma"  : entity.sigma,
            f"{prefix}-maximum": entity.maximum,
            f"{prefix}-minimum": entity.minimum
        }

        if  isinstance(entity, Handle):
            entity_as_json.update({
                f"{prefix}-role"    : entity.role.name,
                f"{prefix}-position": {
                    "x": entity.pos().x(),
                    "y": entity.pos().y()
                },
                f"{prefix}-scenepos": {
                    "x": entity.scenePos().x(),
                    "y": entity.scenePos().y()
                }
            })

        return entity_as_json

    @staticmethod
    @validator
    def json_to_entity(json_data: dict):
        """
        Deserializes a JSON string to an `Entity` instance.
        """
        prefix = "variable" if json_data.get("variable-eclass") else "parameter"
        entity = Entity(
            eclass = EntityClass[json_data.get(f"{prefix}-eclass", "VAR")],
            symbol = json_data.get(f"{prefix}-symbol", ''),
            strid  = json_data.get(f"{prefix}-strid", '')
        )

        entity.label   = json_data.get(f"{prefix}-label", '')
        entity.units   = json_data.get(f"{prefix}-units", '')
        entity.info    = json_data.get(f"{prefix}-info", '')

        entity._data = Entity.Dynamic(
            value   = json_data.get(f"{prefix}-value"  , np.nan),
            sigma   = json_data.get(f"{prefix}-sigma"  , np.nan),
            maximum = json_data.get(f"{prefix}-maximum", np.nan),
            minimum = json_data.get(f"{prefix}-minimum", np.nan),
        )

        entity._bounds = Entity.Boundary(
            start_time = json_data.get(f"{prefix}-start_time", np.nan),
            final_time = json_data.get(f"{prefix}-final_time", np.nan),
            delta_time = json_data.get(f"{prefix}-delta_time", np.nan)
        )

        return entity

    @staticmethod
    @validator
    def serialize(item: QGraphicsItem):
        """
        Serializes a QGraphicsItem to a JSON string.
        :param item:
        :return:
        """
        # If the item is a node:
        if  isinstance(item, Node):

            # Variable(s):
            variables = [
                JsonIO.entity_to_json(var)
                for var, state in item[EntityClass.VAR].items()
                if  state == EntityState.ACTIVE
            ]

            # Parameter(s):
            parameters = [
                JsonIO.entity_to_json(par)
                for par in item[EntityClass.PAR]
            ]

            # Equation(s):
            equations = item[EntityClass.EQN]

            # JSON-composite:
            return {
                "node-title": item.name,  # Node's title
                "node-delta": item.boundingRect().height() - 150,  # Node's height
                "node-scenepos": {  # Node's scene-position
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                },
                "parameters": parameters,  # Node's active parameters
                "variables" : variables,  # Node's active variables
                "equations" : equations  # Node's equations
            }

        # If the item is a terminal:
        if  isinstance(item, StreamTerminal):
            return {
                "terminal-role"  : item.handle.role.name,
                "terminal-label" : item.handle.label,
                "terminal-strid" : item.handle.strid,
                "terminal-scenepos": {
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                }
            }

        # If the item is a connector:
            # If the instance is a connector, serialize the connector's attributes:
        if isinstance(item, Connector):
            # Create JSON-object:
            return {
                "origin-parent-uid": item.origin.parentItem().uid,
                "origin-role": item.origin.role.name,
                "origin-label": item.origin.label,
                "origin-scenepos": {
                    "x": item.origin.scenePos().x(),
                    "y": item.origin.scenePos().y()
                },
                "target-parent-uid": item.target.parentItem().uid,
                "target-role": item.target.role.name,
                "target-label": item.target.label,
                "target-scenepos": {
                    "x": item.target.scenePos().x(),
                    "y": item.target.scenePos().y()
                }
            }

        return None

    @staticmethod
    def encode(canvas):
        """
        Encodes a schematic as a JSON-formatted string.
        :param canvas:
        """
        from tabs.schema.canvas import Canvas

        item_list = (
            canvas.selectedItems() if canvas.selectedItems() else
            [item for item, state in canvas.db.node.items() if state == EntityState.ACTIVE] +   # Active nodes
            [item for item, state in canvas.db.term.items() if state == EntityState.ACTIVE] +   # Active terminals
            [item for item, state in canvas.db.conn.items() if state == EntityState.ACTIVE]     # Active connectors
        )

        # Fetch serialized JSON objects for each item-type:
        node_array = [JsonIO.serialize(item) for item in item_list if isinstance(item, Node)]
        conn_array = [JsonIO.serialize(item) for item in item_list if isinstance(item, Connector)]
        term_array = [JsonIO.serialize(item) for item in item_list if isinstance(item, StreamTerminal)]

        # Initialize JSON objects:
        schematic = {
            "NODES": node_array,  # Add all active nodes
            "TERMINALS": term_array,  # Add all active terminals
            "CONNECTORS": conn_array  # Add all active connectors
        }

        # Return JSON string:
        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode(canvas, json_string: str):
        """
        Decodes a JSON-formatted string into a schematic on the given canvas.
        :param canvas: The canvas to draw the schematic on.
        :param json_string: The JSON string to decode.
        """
        from tabs.schema.canvas import Canvas

        # Read the JSON string:
        # Initialize convenience-variables:
        root  = json.loads(json_string)
        batch = BatchActions([])

        # Parse node-data:
        for node_json in root.get("NODES", []):

            # Read node-attributes:
            delta = node_json.get("node-delta", 0)
            title = node_json.get("node-title", "")
            npos  = QPointF(
                node_json.get("node-scenepos").get("x"),
                node_json.get("node-scenepos").get("y")
            )

            # Create the node and set attributes:
            node = canvas.create_node(npos, False)
            node.name = title
            node.resize(int(delta))

            # Add the node to the canvas:
            canvas.addItem(node)
            canvas.db.node[node] = EntityState.ACTIVE

            # Add action to the batch:
            batch.add_to_batch(CreateNodeAction(canvas, node))

            # Add handles to the node:
            for var_json in node_json.get("variables", []):

                role = var_json.get(f"variable-role", "")               # Get the variable's role (INP/OUT)
                npos = QPointF(
                    var_json.get(f"variable-position", {}).get("x"),    # Get the x-coordinate
                    var_json.get(f"variable-position", {}).get("y")     # Get the y-coordinate
                )

                # If the role is not specified, attempt to infer it from the variable's symbol:
                if  not role:
                    role = "INP" if var_json.get("variable-symbol", "").startswith("R") else "OUT"

                # Create a new handle and set data:
                handle = node.create_handle(EntityRole[role], npos)

                handle.rename(var_json.get("variable-label", ""))
                handle.import_data(JsonIO.json_to_entity(var_json), exclude='symbol')

                # Add action to the batch:
                batch.add_to_batch(CreateHandleAction(node, handle))

            # Add parameters to the node:
            for par_json in node_json.get("parameters", []):

                entity = Entity(
                    EntityClass.PAR,
                    par_json.get("parameter-symbol"),
                    par_json.get("parameter-strid")
                )

                node[EntityClass.PAR].append(entity)

        # Parse terminals:
        for term_json in root.get("TERMINALS") or []:

            # Get the terminal's role and coordinates:
            role = EntityRole.INP if term_json.get("terminal-role") == "INP" else EntityRole.OUT
            tpos = QPointF(
                term_json.get("terminal-scenepos").get("x"),
                term_json.get("terminal-scenepos").get("y")
            )

            # Create terminal:
            terminal = canvas.create_term(role)
            terminal.setPos(tpos)

            terminal.handle.rename(term_json.get("terminal-label"))
            terminal.handle.set_stream(term_json.get("terminal-strid", ""), canvas.db.kind[term_json.get("terminal-strid", "")])
            terminal.handle.sig_item_updated.emit()

            # Add terminal to the database and canvas:
            canvas.addItem(terminal)
            canvas.db.term[terminal] = EntityState.ACTIVE

            # Add action to the batch:
            batch.add_to_batch(CreateStreamAction(canvas, terminal))

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

            origin = canvas.itemAt(opos, QTransform())  # Origin-reference
            target = canvas.itemAt(tpos, QTransform())  # Target-reference

            if not isinstance(origin, Handle):    continue
            if not isinstance(target, Handle):    continue

            # Create a new connector:
            connector = Connector(canvas.create_cuid(),
                                  origin,
                                  target)

            # Add connector to database and canvas:
            canvas.db.conn[connector] = EntityState.ACTIVE
            canvas.addItem(connector)

            # Add connector-creation action to batch:
            batch.add_to_batch(ConnectHandleAction(canvas, connector))

        # Execute batch-actions:
        canvas.manager.do(batch)