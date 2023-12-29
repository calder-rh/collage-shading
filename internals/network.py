from pymel.core import *
import re


def shading_node_makers(prefix, node_set, delete_setting):
    node_makers = {}

    def generic_node_maker(**generic_kwargs):
        def node_maker(node_type, node_name, **kwargs):
            name = prefix + node_name
            if objExists(name):
                if delete_setting:
                    delete(name)
                else:
                    return PyNode(name)
            node = shadingNode(node_type, name=name, **(generic_kwargs | kwargs))
            node_set.add(node)
            return node
        return node_maker
    
    node_makers['utility'] = generic_node_maker(asUtility=True)
    node_makers['texture'] = generic_node_maker(asTexture=True)
    node_makers['shader'] = generic_node_maker(asShader=True)

    def expression_maker(node_name, attributes, expr):
        name = prefix + node_name
        if objExists(name):
            if delete_setting:
                delete(name)
            else:
                return PyNode(name)
        node = expression(n=name)
        node.setDefaultObject(node)
        for attribute in attributes:
            if isinstance(attribute, str):
                addAttr(node, ln=attribute)
            elif isinstance(attribute, dict):
                addAttr(node, **attribute)
                
                if 'at' in attribute:
                    attribute_type = attribute['at']
                    if attribute_type in ['float2', 'float3']:
                        parent_name = attribute['ln']
                        for axis in 'XYZ'[:int(attribute_type[-1])]:
                            addAttr(node, ln=parent_name + axis, at='float', parent=parent_name)
            else:
                raise Exception('Attribute input must be a string or dict')
        node.setExpression(expr.format(this=name))
        node_set.add(node)
        return node
        
    node_makers['expression'] = expression_maker

    def blank(node_name):
        name = prefix + node_name
        if objExists(name):
            if delete_setting:
                delete(name)
            else:
                return PyNode(name)
        node = createNode('unknown', name=name)
        node_set.add(node)
        return node

    node_makers['blank'] = blank

    def generic_float_math_node_maker(operation):
        def float_math_node_maker(input1, input2, node_name):
            name = prefix + node_name
            if objExists(name):
                if delete_setting:
                    delete(name)
                else:
                    return PyNode(name).outFloat

            node = shadingNode('floatMath', asUtility=True, name=name)
            node.operation.set(operation)

            if isinstance(input1, nodetypes.FloatMath):
                input1.outFloat.connect(node.floatA)
            elif isinstance(input1, general.Attribute):
                input1.connect(node.floatA)
            else:
                node.floatA.set(input1)

            if isinstance(input2, nodetypes.FloatMath):
                input2.outFloat.connect(node.floatB)
            elif isinstance(input2, general.Attribute):
                input2.connect(node.floatB)
            else:
                node.floatB.set(input2)
            
            node_set.add(node)
            return node.outFloat
        return float_math_node_maker
    
    node_makers['add'] = generic_float_math_node_maker(0)
    node_makers['subtract'] = generic_float_math_node_maker(1)
    node_makers['multiply'] = generic_float_math_node_maker(2)
    node_makers['divide'] = generic_float_math_node_maker(3)
    node_makers['power'] = generic_float_math_node_maker(6)

    def poly_node_maker(function, node_name, **kwargs):
        name = prefix + node_name
        if objExists(name):
            if delete_setting:
                delete(name)
            else:
                return (PyNode(name), None)
        
        return function(name=name, **kwargs)
    
    node_makers['poly'] = poly_node_maker

    def universal_node_maker(function, node_name, **kwargs):
        name = prefix + node_name
        if objExists(name):
            if delete_setting:
                delete(name)
            else:
                return PyNode(name)
        
        return function(name=name, **kwargs)
    
    node_makers['make'] = universal_node_maker

    return node_makers


class Network:
    reserved_keys = ['utility', 'texture', 'shader', 'expression', 'blank', 'add', 'subtract', 'multiply', 'divide', 'poly', 'make', 'nodes', 'subnetworks', 'node_keys', '__dict__', 'add_keys']
    all_abbreviations = {}
    
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.created_networks = {}
        if not hasattr(cls, 'abbreviation'):
            cls.abbreviation = ''.join(re.findall(r'[A-Z]', cls.__name__)).lower()
        if not hasattr(cls, 'delete'):
            cls.delete = True

        if cls.relevant_context and cls.abbreviation and cls.abbreviation in Network.all_abbreviations:
            raise Exception(f'Abbreviation conflict: {cls.__name__}, {Network.all_abbreviations[cls.abbreviation].__name__}')
        Network.all_abbreviations[cls.abbreviation] = cls

        _original_init = cls.__init__
        def new_init(self, context, *args, **kwargs):
            pass

        cls.__init__ = new_init
        cls._original_init = _original_init

    def __new__(cls, context, *args, **kwargs):
        context_pairs = [(key, context[key]) for key in cls.relevant_context if key in context]
        context_strings = [key + '_' + value for key, value in context_pairs]
        context_string_dict = {key: key + '_' + value for key, value in context_pairs}
        context_tuple = tuple(pair[1] for pair in context_pairs)

        if cls.relevant_context:
            prefix = cls.abbreviation + '___' + '__'.join(context_strings) + '___'
        elif hasattr(cls, 'prefix') and cls.prefix:
            prefix = cls.prefix
        else:
            prefix = ''

        if context_tuple in cls.created_networks:
            result = cls.created_networks[context_tuple]
            return result
        else:
            if isinstance(cls.delete, list):
                delete_regex = '^(?!.*:)' + ''.join([f'(?=.*__{context_string_dict[key]}__)' for key in cls.delete])
                if delete_regex:
                    for node in ls(regex='.*___.*'):
                        if re.search(delete_regex, node.name()) and objExists(node):
                            delete(node)

            result = super().__new__(cls)
            result.nodes = set()
            result.subnetworks = set()
            result.node_keys = {}
            result.__dict__ |= shading_node_makers(prefix, result.nodes, cls.delete != False)
            result.add_keys = True
            result.prefix = prefix
            result._original_init(context, *args, **kwargs)
            cls.created_networks[context_tuple] = result
            return result

    def build(self, network, add_keys=True):
        self.subnetworks.add(network)
        if add_keys:
            self.node_keys |= network.node_keys
            self.__dict__ |= network.node_keys
        return network
    
    def destroy(self):
        for node in self.nodes:
            if objExists(node):
                delete(node)
        for network in self.subnetworks:
            network.destroy()

    def __setattr__(self, key, value):
        if key not in Network.reserved_keys:
            self.node_keys[key] = value
        self.__dict__[key] = value
