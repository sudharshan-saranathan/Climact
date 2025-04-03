import json

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform, QColor

from widgets.schema import graph

class JsonLib:

    @staticmethod
    def serialize(item):

        if isinstance(item, graph.Node):

            handles     = []
            equations   = []
            parameters  = []

            for handle in item[graph.Stream.INP] + item[graph.Stream.OUT]:

                if handle is not None:
                    handle_obj = {
                        "handle-snap"       : handle.snap,
                        "handle-color"      : handle.color.name(),
                        "handle-info"       : handle.info,
                        "handle-unit"       : handle.unit,
                        "handle-label"      : handle.label,
                        "handle-symbol"     : handle.symbol,
                        "handle-stream"     : str(handle.stream()),
                        "handle-category"   : handle.category,
                        "handle-value"      : handle.value,
                        "handle-lower"      : handle.lower,
                        "handle-upper"      : handle.upper,
                        "handle-sigma"      : handle.sigma,
                        "handle-position": {
                            "x": handle.pos().x(),
                            "y": handle.pos().y()
                        }
                    }
                    handles.append(handle_obj)

            for parameter in item[graph.Stream.PAR]:
                parameter_obj = {
                    "parameter-id"          : parameter.id,
                    "parameter-info"        : parameter.info,
                    "parameter-unit"        : parameter.unit,
                    "parameter-label"       : parameter.label,
                    "parameter-symbol"      : parameter.symbol,
                    "parameter-category"    : parameter.category,
                    "parameter-value"       : parameter.value,
                    "parameter-lower"       : parameter.lower,
                    "parameter-upper"       : parameter.upper,
                    "parameter-sigma"       : parameter.sigma,
                }
                parameters.append(parameter_obj)

            for equation in item.equations:
                equations.append(equation)

            # Final JSON custom
            node_object = {
                "handles"    : handles,
                "node-name"  : item.name(),
                "node-type"  : 0,
                "node-height": item.boundingRect().height(),
                "node-position": {
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                },
                "parameters" : parameters,
                "equations"  : equations
            }

            return node_object

        elif isinstance(item, graph.Connector):

            connection_obj = {
                "connection-origin": {
                    "x": item.origin.scenePos().x(),
                    "y": item.origin.scenePos().y()
                },
                "connection-target": {
                    "x": item.target.scenePos().x(),
                    "y": item.target.scenePos().y()
                }
            }

            return connection_obj

        return None

    @staticmethod
    def encode_json():

        from widgets.schema.canvas import Canvas

        schematic  = {}
        node_array = []
        link_array = []

        # Serialize nodes
        for node in Canvas.nodes:
            if node is not None:
                node_array.append(JsonLib.serialize(node))

        # Serialize connectors:
        for connector in Canvas.edges:
            if connector is not None:
                link_array.append(JsonLib.serialize(connector))

        schematic["NODES"] = node_array
        schematic["CONNECTORS"] = link_array

        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode_json(code: str, canvas):

        root = json.loads(code)

        from widgets.schema.canvas import Canvas
        if not isinstance(canvas, Canvas):
            return

        narr = root.get("NODES", [])
        carr = root.get("CONNECTORS", [])

        for element in narr:

            xp   = element.get("node-position", {}).get("x", 0.0)
            yp   = element.get("node-position", {}).get("y", 0.0)
            spos = QPointF(xp, yp)

            _name = element.get("node-name", "")
            _type = element.get("node-type", 0)

            node   = canvas.create_node(_name, spos)
            height = int(element.get("node-height", {}))
            node.adjust(height - 200)

            for handle_obj in element.get("handles", []):

                snap   = handle_obj.get("handle-snap")
                stream = handle_obj.get("handle-stream", 0)
                stream = graph.Stream.INP if stream == "Stream.INP" else graph.Stream.OUT
                xpos   = handle_obj.get("handle-position", {}).get("x", 0.0)
                ypos   = handle_obj.get("handle-position", {}).get("y", 0.0)

                handle = node.create_handle(
                    QPointF(xpos, ypos),
                    node.construct_symbol(stream),
                    stream,
                    False
                )

                value = handle_obj.get("handle-value", "")
                lower = handle_obj.get("handle-lower", "")
                upper = handle_obj.get("handle-upper", "")
                sigma = handle_obj.get("handle-sigma", "")

                handle.category = handle_obj.get("handle-category", "")
                handle.symbol   = handle_obj.get("handle-symbol", "")
                handle.label    = handle_obj.get("handle-label", "")
                handle.info     = handle_obj.get("handle-info", "")
                handle.unit     = handle_obj.get("handle-unit", "")
                handle.color    = QColor(handle_obj.get("handle-color", ""))
                handle.snap     = snap

                try:
                    handle.value = float(value)
                    handle.lower = float(lower)
                    handle.upper = float(upper)
                    handle.sigma = float(sigma)

                except TypeError as exception:
                    pass

            # Deserialize parameters
            for param_obj in element.get("parameters", []):
                resource = graph.Resource()

                value = param_obj.get("parameter-value", "")
                lower = param_obj.get("parameter-lower", "")
                upper = param_obj.get("parameter-upper", "")
                sigma = param_obj.get("parameter-sigma", "")

                resource.id       = param_obj.get("parameter-id", "")
                resource.info     = param_obj.get("parameter-info", "")
                resource.unit     = param_obj.get("parameter-unit", "")
                resource.label    = param_obj.get("parameter-label", "")
                resource.symbol   = param_obj.get("parameter-symbol", "")
                resource.category = param_obj.get("parameter-category", "")

                try:
                    resource.value = float(value)
                    resource.lower = float(lower)
                    resource.upper = float(upper)
                    resource.sigma = float(sigma)

                except TypeError as exception:
                    pass

                node[graph.Stream.PAR].append(resource)

            # Deserialize equations
            for equation in element.get("equations", []):
                node.equations.append(equation)

        # Deserialize connectors
        for json_obj in root.get("CONNECTORS", []):

            sxpos = json_obj.get("connection-origin", {}).get("x", 0.0)
            sypos = json_obj.get("connection-origin", {}).get("y", 0.0)
            txpos = json_obj.get("connection-target", {}).get("x", 0.0)
            typos = json_obj.get("connection-target", {}).get("y", 0.0)

            origin = canvas.itemAt(QPointF(sxpos, sypos), QTransform())
            target = canvas.itemAt(QPointF(txpos, typos), QTransform())

            origin = origin if isinstance(origin, graph.Handle) else None
            target = target if isinstance(target, graph.Handle) else None

            if origin and target:
                try:
                    connector = graph.Connector(origin, target)
                    connector.sig_item_deleted.connect(canvas.on_item_deleted)

                    canvas.addItem(connector)
                    canvas.edges.append(connector)

                except Exception as e:
                    print(f"Error creating connector: {e}")

