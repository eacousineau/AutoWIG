import time
from mako.template import Template
import re
from path import path
import anydbm
import warnings
from operator import attrgetter
from abc import ABCMeta
from openalea.core.util import camel_case_to_lower, to_camel_case, camel_case_to_upper

from .asg import *
from .tools import subclasses, to_path, lower, remove_templates
from .custom_warnings import NotImplementedOperatorWarning, InheritanceWarning, BackEndWarning
from .held_type import held_type
from .call_policy import call_policy
from .node_path import node_path
from .node_rename import node_rename, PYTHON_OPERATOR, CONST_PYTHON_OPERATOR, NON_CONST_PYTHON_OPERATOR

__all__ = []

def get_boost_python_export(self):
    return False

CodeNodeProxy.boost_python_export = property(get_boost_python_export)

def get_boost_python_export(self):
    return any(dcl.boost_python_export for dcl in self.declarations())

def set_boost_python_export(self, boost_python_export):
    for enm in self.enums():
        enm.boost_python_export = boost_python_export
    for cst in self.enum_constants():
        cst.boost_python_export = boost_python_export
    for var in self.variables():
        var.boost_python_export = boost_python_export
    for fct in self.functions():
        fct.boost_python_export = boost_python_export
    for cls in self.classes():
        cls.boost_python_export = boost_python_export
    for nsp in self.namespaces():
        nsp.boost_python_export = boost_python_export

def del_boost_python_export(self):
    for enm in self.enums():
        del enm.boost_python_export
    for cst in self.enum_constants():
        del cst.boost_python_export
    for var in self.variables():
        del var.boost_python_export
    for fct in self.functions():
        del fct.boost_python_export
    for cls in self.classes():
        del cls.boost_python_export
    for nsp in self.namespaces():
        del nsp.boost_python_export

NamespaceProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export, set_boost_python_export, del_boost_python_export

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        return not self.is_smart_pointer and any(spc.boost_python_export for spc in self.specializations(partial=False))

def set_boost_python_export(self, boost_python_export):
    self.asg._nodes[self.node]['_boost_python_export'] = boost_python_export
    for spc in self.specializations(partial=False):
        spc.boost_python_export = boost_python_export

def del_boost_python_export(self):
    self.asg._nodes[self.node].pop('_boost_python_export', None)
    for spc in self.specializations(partial=False):
        del spc.boost_python_export

ClassTemplateProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
#ClassTemplatePartialSpecializationProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export, set_boost_python_export, del_boost_python_export

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        parent = self.parent
        if isinstance(parent, ClassProxy) and not(self.access == 'public' and parent.boost_python_export):
            return False
        else:
            return True

def set_boost_python_export(self, boost_python_export):
    if not isinstance(boost_python_export, (bool, BoostPythonExportFileProxy)):
        raise TypeError('\'boost_python_export\' parameter')
    if boost_python_export:
        del self.boost_python_export
        if not self.boost_python_export:
            raise ValueError('\'boost_python_export\' parameter')
    if isinstance(boost_python_export, BoostPythonExportFileProxy):
        scope = boost_python_export.scope
        if scope is None or scope == self.parent:
            del self.boost_python_export
            boost_python_export._wraps.add(self.node)
            boost_python_export = boost_python_export.node
    else:
        del self.boost_python_export
    self.asg._nodes[self.node]['_boost_python_export'] = boost_python_export

def del_boost_python_export(self):
    if isinstance(self.boost_python_export, BoostPythonExportFileProxy):
        self.boost_python_export._wraps.remove(self.node)
    self.asg._nodes[self.node].pop('_boost_python_export', None)

EnumConstantProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
EnumProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
DestructorProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
ClassProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
TypedefProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        parent = self.parent
        if isinstance(parent, ClassProxy) and not(self.access == 'public' and parent.boost_python_export):
            return False
        else:
            return not self.is_smart_pointer

ClassTemplateSpecializationProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export

def is_invalid_pointer(edge):
    return edge.nested.is_pointer or edge.is_pointer and isinstance(edge.target, FundamentalTypeProxy)

def is_invalid_reference(edge):
    return edge.is_rvalue_reference

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        parent = self.parent
        if isinstance(parent, ClassProxy) and not(self.access == 'public' and parent.boost_python_export):
            return False
        else:
            return not(is_invalid_pointer(self.type) or self.type.is_reference)

VariableProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        parent = self.parent
        if isinstance(parent, ClassProxy) and not(self.access == 'public' and parent.boost_python_export):
            return False
        else:
            not(any(is_invalid_pointer(prm.type) or is_invalid_reference(prm.type) for prm in self.parameters))

ConstructorProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export

def is_valid_operator(node):
    if node.localname.startswith('operator'):
        operator = node.localname.strip('operator').strip()
        if operator in ['++', '--']:
            return len(node.parameters) == 1
        else:
            return operator in PYTHON_OPERATOR or node.is_const and operator in CONST_PYTHON_OPERATOR or not node.is_const and operator in NON_CONST_PYTHON_OPERATOR
    else:
        return True

def get_boost_python_export(self):
    if hasattr(self, '_boost_python_export'):
        boost_python_export = self._boost_python_export
        if isinstance(boost_python_export, bool):
            return boost_python_export
        else:
            return self.asg[boost_python_export]
    else:
        parent = self.parent
        if isinstance(parent, ClassProxy) and not(self.access == 'public' and parent.boost_python_export):
            return False
        else:
            return is_valid_operator(self) and not(is_invalid_pointer(self.result_type) or is_invalid_reference(self.result_type) or any(is_invalid_pointer(prm.type) or is_invalid_reference(prm.type) for prm in self.parameters))

FunctionProxy.boost_python_export = property(get_boost_python_export, set_boost_python_export, del_boost_python_export)
del get_boost_python_export, set_boost_python_export, del_boost_python_export

class BoostPythonExportFileProxy(FileProxy):

    language = 'c++'

    def __init__(self, asg, node):
        super(BoostPythonExportFileProxy, self).__init__(asg, node)
        if not hasattr(self, '_wraps'):
            self.asg._nodes[self.node]['_wraps'] = set()

    @property
    def wraps(self):
        wraps = [self.asg[wrap] for wrap in self._wraps]
        return [wrap for wrap in wraps if not isinstance(wrap, ClassProxy)] + sorted([wrap for wrap in wraps if isinstance(wrap, ClassProxy)], key = lambda cls: cls.depth)

def get_depth(self):
    if not hasattr(self, '_depth'):
        return 0
    else:
        return self._depth

def set_depth(self, depth):
    self.asg._nodes[self.node]['_depth'] = depth

def del_depth(self):
    self.asg._nodes[self.node].pop('_depth')

BoostPythonExportFileProxy.depth = property(get_depth, set_depth, del_depth)
del get_depth, set_depth, del_depth

def get_scope(self):
    if hasattr(self, '_scope'):
        return self._scope

def set_scope(self, scope):
    self.asg._nodes[self.node]['_scope'] = scope

def del_scope(self):
    self.asg._nodes[self.node].pop('_scope')

BoostPythonExportFileProxy.scope = property(get_scope, set_scope, del_scope)
del get_scope, set_scope, del_scope

def get_boost_python_module(self):
    if hasattr(self, '_boost_python_module'):
        return self.asg[self._boost_python_module]

def set_boost_python_module(self, boost_python_module):
    _boost_python_module = self.boost_python_module
    if _boost_python_module:
        _boost_python_module._boost_python_exports.remove(self.node)
    self.asg._nodes[self.node]['_boost_python_module'] = boost_python_module
    self.boost_python_module._boost_python_exports.add(self.node)

def del_boost_python_module(self):
    boost_python_module = self.boost_python_module
    if boost_python_module:
        boost_python_module._boost_python_exports.remove(self.node)
    self.asg._nodes[self.node].pop('_boost_python_module', None)

BoostPythonExportFileProxy.boost_python_module = property(get_boost_python_module, set_boost_python_module, del_boost_python_module)
del get_boost_python_module, set_boost_python_module, del_boost_python_module

class BoostPythonExportTemplateFileProxy(BoostPythonExportFileProxy):

    language = 'c++'

    HEADER = Template(text=r"""\
#include <boost/python.hpp>\
% for header in headers:

    % if header.language == 'c':
extern "C" { \
    % endif
#include <${header.path}>\
    % if header.language == 'c':
 }\
    % endif
% endfor""")

    SCOPE = Template(text=r"""\
% for scope in scopes:
        std::string ${node_rename(scope, scope=True) + '_' + scope.hash}_name = boost::python::extract< std::string >(boost::python::scope().attr("__name__") + ".${node_rename(scope, scope=True)}");
        boost::python::object ${node_rename(scope, scope=True) + '_' + scope.hash}_module(boost::python::handle<  >(boost::python::borrowed(PyImport_AddModule(${node_rename(scope, scope=True) + '_' + scope.hash}_name.c_str()))));
        boost::python::scope().attr("${node_rename(scope, scope=True)}") = ${node_rename(scope, scope=True) + '_' + scope.hash}_module;
        boost::python::scope ${node_rename(scope, scope=True) + '_' + scope.hash}_scope = ${node_rename(scope, scope=True) + '_' + scope.hash}_module;\
% endfor""")

    CONSTANT = Template(text="""\
        boost::python::scope().attr("${node_rename(constant)}") = (int)(${constant.globalname});\
""")

    ENUM = Template(text=r"""\
        boost::python::enum_< ${enum.globalname} >("${node_rename(enum)}")\
    % for constant in enum.constants:
        % if constant.boost_python_export:

            .value("${node_rename(constant)}", ${constant.globalname})\
        % endif
    % endfor
;""")

    VARIABLE = Template(text="""\
        boost::python::scope().attr("${node_rename(variable)}") = ${variable.globalname};\
""")

    FUNCTION = Template(text=r"""\
    % if function.is_overloaded:
        ${function.result_type.globalname} (*function_pointer_${function.hash})(${", ".join(parameter.type.globalname for parameter in function.parameters)}) = ${function.globalname};
    % endif
        boost::python::def("${node_rename(function)}", \
    % if function.is_overloaded:
function_pointer_${function.hash}\
    % else:
${function.globalname}\
    % endif
    % if call_policy(function):
, ${call_policy(function)}\
    % endif
);""")

    CLASS = Template(text=r"""\
    % for method in cls.methods():
        % if method.boost_python_export and method.access == 'public' and method.is_overloaded:
        ${method.result_type.globalname} (\
            % if not method.is_static:
${method.parent.globalname.replace('class ', '').replace('struct ', '').replace('union ', '')}::\
            % endif
*method_pointer_${method.hash})(${", ".join(parameter.type.globalname for parameter in method.parameters)})\
            % if method.is_const:
 const\
            % endif
 = \
            % if not method.is_static:
&\
            % endif
${method.globalname};
        % endif
    % endfor
        boost::python::class_< ${cls.globalname}, \
    % if held_type(cls):
${held_type(cls)}\
    % else:
${cls.globalname} *\
    % endif
    % if any(base.access == 'public' for base in cls.bases() if base.access == 'public' and base.boost_python_export):
, boost::python::bases< ${", ".join(base.globalname for base in cls.bases() if base.access == 'public' and base.boost_python_export)} >\
    % endif
    % if not cls.is_copyable or cls.is_abstract:
, boost::noncopyable\
    % endif
 >("${node_rename(cls)}", boost::python::no_init)\
    % if not cls.is_abstract:
        % for constructor in cls.constructors:
            % if constructor.access == 'public' and constructor.boost_python_export:

            .def(boost::python::init< ${", ".join(parameter.type.globalname for parameter in constructor.parameters)} >())\
            % endif
        % endfor
    % endif
    % for method in cls.methods():
        % if method.access == 'public' and method.boost_python_export:
            % if not hasattr(method, 'as_constructor') or not method.as_constructor:

            .def("${node_rename(method)}", \
                % if method.is_overloaded:
method_pointer_${method.hash}\
                % else:
&${method.globalname}\
                % endif
                % if call_policy(method):
, ${call_policy(method)}\
                % endif
)\
            % else:

            .def("__init__", boost::python::make_constructor(\
                % if method.is_overloaded:
${method.localname}_${method.hash}
                % else:
${method.globalname}\
))\
                % endif
            % endif
        % endif
    % endfor
    % for methodname in set([node_rename(method) for method in cls.methods() if method.access == 'public' and method.is_static and method.boost_python_export]):

            .staticmethod("${methodname}")\
    % endfor
    % for field in cls.fields():
        % if field.access == 'public' and field.boost_python_export:
            % if field.type.is_const:

            .def_readonly\
            % else:

            .def_readwrite\
            % endif
("${node_rename(field)}", \
            % if not field.is_static:
&\
            % endif
${field.globalname})\
        % endif
    % endfor
;\
    % if held_type(cls):
        % for bse in cls.bases():
            % if bse.access == 'public' and bse.boost_python_export and held_type(bse):

        boost::python::implicitly_convertible< ${held_type(cls)}, ${held_type(bse)} >();\
            % endif
        % endfor
    % endif""")

    @property
    def is_empty(self):
        return len(self._wraps) == 0

    @property
    def depth(self):
        if self.is_empty:
            return 0
        else:
            depth = 0
            for wrap in self.wraps:
                if isinstance(wrap, ClassProxy):
                    depth = max(wrap.depth, depth)
                elif isinstance(wrap, VariableProxy):
                    target = wrap.type.target
                    if isinstance(target, ClassTemplateSpecializationProxy) and target.is_smart_pointer:
                        target = target.templates[0].target
                    if isinstance(target, ClassProxy):
                        depth = max(target.depth+1, depth)
            return depth

    #@property
    #def headers(self):
    #    if self._held_type is None:
    #        return self.asg.headers(*self.wraps)
    #    else:
    #        return self.asg.headers(self.asg[self._held_type], *self.wraps)

    @property
    def scope(self):
        if len(self._wraps) > 0:
            return self.asg[self.wraps[0]].parent

    @property
    def scopes(self):
        if len(self._wraps) > 0:
            return self.wraps[0].ancestors[1:]
        else:
            return []

    @property
    def content(self):
        if not hasattr(self, '_content') or self._content == "":
            content = self.HEADER.render(headers = self.asg.headers(*self.wraps))
            content += '\n\nvoid ' + self.prefix + '()\n{\n'
            content += self.SCOPE.render(scopes = self.scopes,
                    node_rename = node_rename)
            for arg in self.wraps:
                if isinstance(arg, EnumConstantProxy):
                    content += '\n' + self.CONSTANT.render(constant = arg,
                            node_rename = node_rename)
                elif isinstance(arg, EnumProxy):
                    content += '\n' + self.ENUM.render(enum = arg,
                            node_rename = node_rename)
                elif isinstance(arg, VariableProxy):
                    content += '\n' + self.VARIABLE.render(variable = arg,
                            node_rename = node_rename)
                elif isinstance(arg, FunctionProxy):
                    content += '\n' + self.FUNCTION.render(function = arg,
                            node_rename = node_rename,
                            call_policy = call_policy)
                elif isinstance(arg, ClassProxy):
                    content += '\n' + self.CLASS.render(cls = arg,
                            node_rename = node_rename,
                            held_type = held_type,
                            call_policy = call_policy)
                elif isinstance(arg, TypedefProxy):
                    continue
                else:
                    raise NotImplementedError(arg.__class__.__name__)
            content += '\n}'
            self.content = content
        return self._content

    @content.setter
    def content(self, content):
        self.asg._nodes[self.node]['_content'] = content

    @content.deleter
    def del_content(self):
        self.asg._nodes[self.node].pop('_content', False)

def boost_python_exports(self, pattern=None):
    class _MetaClass(object):
        __metaclass__ = ABCMeta
    _MetaClass.register(BoostPythonExportFileProxy)
    metaclass = _MetaClass
    return self.nodes(pattern=pattern, metaclass=metaclass)

AbstractSemanticGraph.boost_python_exports = boost_python_exports
del boost_python_exports

def export_back_end(asg, directory, prefix='', suffix='.cpp', pattern='.*', proxy=BoostPythonExportTemplateFileProxy, **kwargs):
    directory = asg.add_directory(directory)
    nodes = set()
    for node in asg.declarations(pattern=pattern):
        if node.boost_python_export is True:
            if isinstance(node, EnumConstantProxy) and isinstance(node.parent, EnumProxy) or isinstance(node, (FieldProxy, MethodProxy, ConstructorProxy, DestructorProxy, NamespaceProxy, ClassTemplateProxy, ClassTemplatePartialSpecializationProxy)):
                continue
            else:
                node.boost_python_export = asg.add_file(directory.globalname + node_path(node, prefix=prefix, suffix=suffix), proxy=proxy)
                nodes.add(node.boost_python_export.node)

class BoostPythonModuleFileProxy(FileProxy):

    language = 'c++'

    CONTENT = Template(text=r"""\
#include <boost/python.hpp>

% for export in boost_python_exports:
    % if not export.is_empty:
void ${export.prefix}();
    % endif
% endfor

BOOST_PYTHON_MODULE(${modulename})
{
% for export in boost_python_exports:
    % if not export.is_empty:
    ${export.prefix}();
    %endif
% endfor
}""")


    def __init__(self, asg, node):
        super(BoostPythonModuleFileProxy, self).__init__(asg, node)
        if not hasattr(self, '_boost_python_exports'):
            self.asg._nodes[self.node]['_boost_python_exports'] = set()

    @property
    def boost_python_exports(self):
        if not hasattr(self, '_boost_python_exports'):
            return []
        else:
            return [export for export in sorted([self.asg[export] for export in self._boost_python_exports], key = attrgetter('depth'))]

    @property
    def modulename(self):
        if not hasattr(self, '_modulename'):
            return self.prefix
        else:
            return self._modulename

    @modulename.setter
    def modulename(self, modulename):
        #if modulename == self.localname:
        #    raise ValueError('\'modulename\' parameter')
        self.asg._nodes[self.node]['_modulename'] = modulename

    @modulename.deleter
    def modulename(self):
        self.asg._nodes[self.node].pop('_modulename', self.localname.prefix)

    @property
    def dependencies(self):
        modules = set([self.globalname])
        temp = [wrap for export in self.boost_python_exports for wrap in export.wraps]
        while len(temp) > 0:
            wrap = temp.pop()
            if isinstance(wrap, FunctionProxy):
                boost_python_export = wrap.result_type.target.boost_python_export
                if boost_python_export and not boost_python_export is True:
                    boost_python_module = boost_python_export.boost_python_module
                    if not boost_python_module is None:
                        modules.add(boost_python_module.globalname)
                for prm in wrap.parameters:
                    boost_python_export = prm.type.target.boost_python_export
                    if boost_python_export and not boost_python_export is True:
                        boost_python_module = boost_python_export.boost_python_module
                        if not boost_python_module is None:
                            modules.add(boost_python_module.globalname)
            elif isinstance(wrap, (VariableProxy, TypedefProxy)):
                boost_python_export = wrap.type.target.boost_python_export
                if boost_python_export and not boost_python_export is True:
                    boost_python_module = boost_python_export.boost_python_module
                    if not boost_python_module is None:
                        modules.add(boost_python_module.globalname)
            elif isinstance(wrap, ClassProxy):
                boost_python_export = wrap.boost_python_export
                if boost_python_export and not boost_python_export is True:
                    boost_python_module = boost_python_export.boost_python_module
                    if boost_python_export and not boost_python_export is True:
                        modules.add(boost_python_module.globalname)
                temp.extend([bse for bse in wrap.bases() if bse.access == 'public'])
                temp.extend([dcl for dcl in wrap.declarations() if dcl.access == 'public'])
            elif isinstance(wrap, ClassTemplateProxy):
                boost_python_export = wrap.boost_python_export
                if boost_python_export and not boost_python_export is True:
                    boost_python_module = boost_python_export.boost_python_module
                    if boost_python_export and not boost_python_export is True:
                        modules.add(boost_python_module.globalname)
        modules.remove(self.globalname)
        return [self.asg[module] for module in modules]

    @property
    def depth(self):
        dependencies = self.dependencies
        if len(dependencies) == 0:
            return 0
        else:
            return max(dependency.depth for dependency in dependencies) + 1

    @property
    def content(self):
        if not hasattr(self, '_content') or self._content == "":
            self.content = self.CONTENT.render(boost_python_exports = self.boost_python_exports,
                    modulename = self.modulename)
        return self._content

    @content.setter
    def content(self, content):
        self.asg._nodes[self.node]['_content'] = content

    @content.deleter
    def content(self):
        self.asg._nodes[self.node].pop('_content', '')

def boost_python_modules(self, pattern=None):
    class _MetaClass(object):
        __metaclass__ = ABCMeta
    _MetaClass.register(BoostPythonModuleFileProxy)
    metaclass = _MetaClass
    return self.nodes(pattern=pattern, metaclass=metaclass)

AbstractSemanticGraph.boost_python_modules = boost_python_modules
del boost_python_modules

def module_back_end(asg, filename, **kwargs):
    if isinstance(filename, BoostPythonModuleFileProxy):
        filename = filename.gobalname
    if filename in asg:
        boost_python_module = asg[filename]
    else:
        boost_python_module = asg.add_file(filename,
                proxy = kwargs.pop('proxy', BoostPythonModuleFileProxy),
                package = kwargs.pop('package', None))
    pattern = kwargs.pop('pattern', boost_python_module.parent.globalname + '.*')
    for export in asg.boost_python_exports(pattern):
        export.boost_python_module = boost_python_module
    #export = kwargs.pop('export', BoostPythonExportTemplateFileProxy)
    #suffix = modulenode.suffix
    #directory = modulenode.parent.globalname
    #pattern = kwargs.pop('pattern', None)
    #for node in asg.nodes(pattern=pattern):
    #    if isinstance(node, CodeNodeProxy) and node.boost_python_export is True:
    #        if isinstance(node, EnumConstantProxy):
    #            parent = node.parent
    #            if not isinstance(parent, EnumProxy) and (not isinstance(parent, ClassProxy) or node.access == 'public'):
    #                exportnode = modulenode.add_boost_python_export(directory + node_path(node, prefix='constants_', suffix=suffix), proxy = export)
    #                exportnode.add_wrap(node)
    #        elif isinstance(node, EnumProxy):
    #            parent = node.parent
    #            if not isinstance(parent, ClassProxy) or node.access == 'public':
    #                exportnode = modulenode.add_boost_python_export(directory + node_path(node, prefix='enumeration_', suffix=suffix), proxy = export)
    #                exportnode.add_wrap(node)
    #        elif isinstance(node, VariableProxy) and not isinstance(node, FieldProxy):
    #            exportnode = modulenode.add_boost_python_export(directory + node_path(node, prefix='variable_', suffix=suffix), proxy = export)
    #            exportnode.add_wrap(node)
    #        elif isinstance(node, FunctionProxy) and not isinstance(node, MethodProxy):
    #            exportnode = modulenode.add_boost_python_export(directory + node_path(node, prefix='function_', suffix=suffix), proxy = export)
    #            exportnode.add_wrap(node)
    #        elif isinstance(node, ClassProxy):
    #            if not isinstance(node, ClassTemplateSpecializationProxy) or not node.is_smart_pointer:
    #                parent = node.parent
    #                if not isinstance(parent, ClassProxy) or node.access == 'public':
    #                    exportnode = modulenode.add_boost_python_export(directory + node_path(node, prefix='class_', suffix=suffix), proxy = export)
    #                    exportnode.add_wrap(node)
    #        elif isinstance(node, TypedefProxy):
    #            parent = node.parent
    #            if not isinstance(parent, ClassProxy) or node.access == 'public':
    #                exportnode = modulenode.add_boost_python_export(directory + node_path(parent, prefix='typedefs_', suffix=suffix), proxy = export)
    #                exportnode.add_wrap(node)
    #        elif isinstance(node, ClassTemplateProxy):
    #            parent = node.parent
    #            if not isinstance(parent, ClassProxy) or node.access == 'public':
    #                exportnode = modulenode.add_boost_python_export(directory + node_path(parent, prefix='templates_', suffix=suffix), proxy = export)
    #                exportnode.add_wrap(node)

#    if kwargs.pop('closure', False):
#        nodes = []
#        forbidden = set()
#        for node in asg.nodes():
#            if hasattr(node, 'boost_python_export'):
#                if node.boost_python_export and not node.boost_python_export is True:
#                    nodes.append(node)
#                elif not node.boost_python_export:
#                    forbidden.add(node.node)
#                else:
#                    if not isinstance(node, (FieldProxy, MethodProxy, ConstructorProxy)):
#                        node.boost_python_export = False
#                    elif not node.access == 'public':
#                        node.boost_python_export = False
#                    #parent = node.parent
#                    #if not isinstance(parent, ClassProxy) or not node.access == 'public':
#                    #    node.boost_python_export = False
#        while len(nodes) > 0:
#            node = nodes.pop()
#            if not node.node in forbidden:
#                if not node.boost_python_export:
#                    node.boost_python_export = True
#                #parent = node.parent
#                #if not parent.boost_python_export:
#                #    nodes.append(parent)
#                if isinstance(node, (TypedefProxy, VariableProxy)):
#                    target = node.type.target
#                    if not target.node in forbidden:
#                        if not target.boost_python_export:
#                            nodes.append(target)
#                    else:
#                        node.boost_python_export = False
#                elif isinstance(node, FunctionProxy):
#                    result_type = node.result_type.target
#                    if not result_type.node in forbidden and not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
#                        if not result_type.boost_python_export:
#                            nodes.append(result_type)
#                        for parameter in node.parameters:
#                            target = parameter.type.target
#                            if not target.boost_python_export:
#                                nodes.append(target)
#                    else:
#                        node.boost_python_export = False
#                elif isinstance(node, ConstructorProxy):
#                    if not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
#                        for parameter in node.parameters:
#                            target = parameter.type.target
#                            if not target.boost_python_export:
#                                nodes.append(target)
#                    else:
#                        node.boost_python_export = False
#                elif isinstance(node, ClassProxy):
#                    for base in node.bases():
#                        if not base.boost_python_export and base.access == 'public':
#                            nodes.append(base)
#                    for dcl in node.declarations():
#                        if dcl.boost_python_export is True and dcl.access == 'public':
#                            nodes.append(dcl)
#                    if isinstance(node, ClassTemplateSpecializationProxy):
#                        if not node.specialize.boost_python_export:
#                            nodes.append(node.specialize)
#        #for fdt in subclasses(FundamentalTypeProxy):
#        #    if isinstance(fdt.node, basestring) and fdt.node in asg:
#        #        asg[fdt.node].boost_python_export = False
#        #if 'class ::boost::shared_ptr' in asg:
#        #    for spc in asg['class ::boost::shared_ptr'].specializations(partial=False):
#        #        spc.boost_python_export = False
#        #if 'class ::std::smart_ptr' in asg:
#        #    for spc in asg['class ::std::smart_ptr'].specializations(partial=False):
#        #        spc.boost_python_export = False
#        for tdf in asg.typedefs():
#            if isinstance(tdf.boost_python_export, bool) and not tdf.boost_python_export:
#                if not tdf.node in forbidden and tdf.type.target.boost_python_export:
#                    tdf.boost_python_export = True
#                    parent = tdf.parent
#                    while not parent.boost_python_export:
#                        parent.boost_python_export = True
#                        parent = parent.parent
#                else:
#                    tdf.boost_python_export = False

def closure_back_end(asg):
    nodes = []
    forbidden = set()
    for node in asg.nodes():
        if hasattr(node, 'boost_python_export'):
            if node.boost_python_export and not node.boost_python_export is True:
                nodes.append(node)
            elif not node.boost_python_export:
                forbidden.add(node.node)
            elif not isinstance(node, (NamespaceProxy, ClassTemplateProxy, ClassTemplatePartialSpecializationProxy)):
                if not isinstance(node, (FieldProxy, MethodProxy, ConstructorProxy, DestructorProxy)):
                    node.boost_python_export = False
                elif not node.access == 'public':
                    node.boost_python_export = False
                #parent = node.parent
                #if not isinstance(parent, ClassProxy) or not node.access == 'public':
                #    node.boost_python_export = False
    while len(nodes) > 0:
        node = nodes.pop()
        if not node.node in forbidden:
            if not node.boost_python_export:
                node.boost_python_export = True
            #parent = node.parent
            #if not parent.boost_python_export:
            #    nodes.append(parent)
            if isinstance(node, (TypedefProxy, VariableProxy)):
                target = node.type.target
                if not target.node in forbidden:
                    if not target.boost_python_export:
                        nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, FunctionProxy):
                result_type = node.result_type.target
                if not result_type.node in forbidden and not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
                    if not result_type.boost_python_export:
                        nodes.append(result_type)
                    for parameter in node.parameters:
                        target = parameter.type.target
                        if not target.boost_python_export:
                            nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, ConstructorProxy):
                if not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
                    for parameter in node.parameters:
                        target = parameter.type.target
                        if not target.boost_python_export:
                            nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, ClassProxy):
                for base in node.bases():
                    if not base.boost_python_export and base.access == 'public':
                        nodes.append(base)
                for dcl in node.declarations():
                    if dcl.boost_python_export is True and dcl.access == 'public':
                        nodes.append(dcl)
                #if isinstance(node, ClassTemplateSpecializationProxy):
                #    if not node.specialize.boost_python_export:
                #        nodes.append(node.specialize)
    #for fdt in subclasses(FundamentalTypeProxy):
    #    if isinstance(fdt.node, basestring) and fdt.node in asg:
    #        asg[fdt.node].boost_python_export = False
    #if 'class ::boost::shared_ptr' in asg:
    #    for spc in asg['class ::boost::shared_ptr'].specializations(partial=False):
    #        spc.boost_python_export = False
    #if 'class ::std::smart_ptr' in asg:
    #    for spc in asg['class ::std::smart_ptr'].specializations(partial=False):
    #        spc.boost_python_export = False
    for tdf in asg.typedefs():
        if isinstance(tdf.boost_python_export, bool) and not tdf.boost_python_export:
            if not tdf.node in forbidden and tdf.type.target.boost_python_export:
                tdf.boost_python_export = True
                parent = tdf.parent
                while not parent.boost_python_export:
                    parent.boost_python_export = True
                    parent = parent.parent
            else:
                tdf.boost_python_export = False

class BoostPythonImportFileProxy(FileProxy):

    language = 'py'

    IMPORTS = Template(text=r"""\
% for module in modules:
import ${module.package}.${module.modulename}
% endfor""")

    @property
    def content(self):
        if not hasattr(self, '_content') or self._content == "":
            dependencies = self.module.dependencies + [self.module]
            self.content = self.IMPORTS.render(modules = sorted(dependencies, key = lambda dependency: dependency.depth))
        return self._content

    @content.setter
    def content(self, content):
        self.asg._nodes[self.node]['_content'] = content

    @content.deleter
    def del_content(self):
        self.asg._nodes[self.node].pop('_content', False)

    @property
    def module(self):
        return self.asg[self._module]

def import_back_end(asg, filename, module, proxy=BoostPythonImportFileProxy):
    if not isinstance(module, BoostPythonModuleFileProxy):
        module = asg[module]
    if isinstance(module, BoostPythonModuleFileProxy):
        module = module.globalname
    else:
        raise ValueError('\'module\' parameter')
    asg.add_file(filename, proxy=proxy, _module=module)
    #for bpm in asg.boost_python_modules(pattern=pattern):
    #    importscript = asg.add_file(bpm.target.globalname + '_' + self.prefix + '.py', proxy=proxy)
    #    importscript.language = 'py'
    #    modules = set()
    #    temp = [wrap for export in bmp.boost_python_exports for wrap in export.wraps]
    #    while len(temp) > 0:
    #        wrap = temp.pop()
    #        if isinstance(wrap, FunctionProxy):
    #            boost_python_export = wrap.result_type.target.boost_python_export
    #            if boost_python_export and not boost_python_export is True:
    #                boost_python_module = boost_python_export.boost_python_module
    #                if not boost_python_module is None:
    #                    modules.add(boost_python_module.globalname)
    #            for prm in wrap.parameters:
    #                boost_python_export = prm.type.target.boost_python_export
    #                if boost_python_export and not boost_python_export is True:
    #                    boost_python_module = boost_python_export.boost_python_module
    #                    if not boost_python_module is None:
    #                        modules.add(boost_python_module.globalname)
    #        elif isinstance(wrap, (VariableProxy, TypedefProxy)):
    #            boost_python_export = wrap.type.target.boost_python_export
    #            if boost_python_export and not boost_python_export is True:
    #                boost_python_module = boost_python_export.boost_python_module
    #                if not boost_python_module is None:
    #                    modules.add(boost_python_module.globalname)
    #        elif isinstance(wrap, ClassProxy):
    #            boost_python_export = wrap.boost_python_export
    #            if boost_python_export and not boost_python_export is True:
    #                boost_python_module = boost_python_export.boost_python_module
    #                if boost_python_export and not boost_python_export is True:
    #                    modules.add(boost_python_module.globalname)
    #            temp.extend([bse for bse in wrap.bases() if bse.access == 'public'])
    #            temp.extend([dcl for dcl in wrap.declarations() if dcl.access == 'public'])
    #        elif isinstance(wrap, ClassTemplateProxy):
    #            boost_python_export = wrap.boost_python_export
    #            if boost_python_export and not boost_python_export is True:
    #                boost_python_module = boost_python_export.boost_python_module
    #                if boost_python_export and not boost_python_export is True:
    #                    modules.add(boost_python_module.globalname)
    #    if bpm.globalname in modules:
    #        modules.remove(bmp.globalname)
    #    # TODO
    #    templates = set()
    #    for export in bpm.boost_python_exports:
    #        for wrap in export.wraps:
    #            if isinstance(wrap, TemplateClassSpecialization):
    #                templates.add(wrap.specialize.node)
    #    templates = [asg[template] for template in templates]
    #    # TODO
    #    #content = [IMPORTS.render(obj = self).strip()]
    #    #    if content[-1] == '':
    #    #        content = content[:-1]
    #    #    else:
    #    #        content[-1] = '# Import C++ dependencies\n' + content[-1]
    #    #    #content.append(self.render_functions())
    #    #    content.append(self.render_templates())
    #    #    #self.TEMPLATES.render(obj = self, node_rename = node_rename,
    #    #    #    camel_case_to_lower = camel_case_to_lower).strip())
    #    #    if content[-1] == '':
    #    #        content = content[:-1]
    #    #    #else:
    #    #    #    content[-1] = '# Import decorators for template instanciations\n' + content[-1]
    #    #    #contents.append(self.SCOPES.render(obj = self).strip())
    #    #    #contents.append(self.TYPEDEFS.render(obj = self).strip())
    #    #    #contents.append(self.SPECIALIZATIONS.render(obj = self).strip())
    #    #    importscript.cont

def closure(asg):
    nodes = []
    forbidden = set()
    for node in asg.nodes():
        if hasattr(node, 'boost_python_export'):
            if node.boost_python_export and not node.boost_python_export is True:
                nodes.append(node)
            elif not node.boost_python_export:
                forbidden.add(node.node)
            else:
                if not isinstance(node, (FieldProxy, MethodProxy, ConstructorProxy)):
                    node.boost_python_export = False
                elif not node.access == 'public':
                    node.boost_python_export = False
                #parent = node.parent
                #if not isinstance(parent, ClassProxy) or not node.access == 'public':
                #    node.boost_python_export = False
    while len(nodes) > 0:
        node = nodes.pop()
        if not node.node in forbidden:
            if not node.boost_python_export:
                node.boost_python_export = True
            #parent = node.parent
            #if not parent.boost_python_export:
            #    nodes.append(parent)
            if isinstance(node, (TypedefProxy, VariableProxy)):
                target = node.type.target
                if not target.node in forbidden:
                    if not target.boost_python_export:
                        nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, FunctionProxy):
                result_type = node.result_type.target
                if not result_type.node in forbidden and not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
                    if not result_type.boost_python_export:
                        nodes.append(result_type)
                    for parameter in node.parameters:
                        target = parameter.type.target
                        if not target.boost_python_export:
                            nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, ConstructorProxy):
                if not any([parameter.type.target.node in forbidden for parameter in node.parameters]):
                    for parameter in node.parameters:
                        target = parameter.type.target
                        if not target.boost_python_export:
                            nodes.append(target)
                else:
                    node.boost_python_export = False
            elif isinstance(node, ClassProxy):
                for base in node.bases():
                    if not base.boost_python_export and base.access == 'public':
                        nodes.append(base)
                for dcl in node.declarations():
                    if dcl.boost_python_export is True and dcl.access == 'public':
                        nodes.append(dcl)
                if isinstance(node, ClassTemplateSpecializationProxy):
                    if not node.specialize.boost_python_export:
                        nodes.append(node.specialize)
    for fdt in subclasses(FundamentalTypeProxy):
        if isinstance(fdt.node, basestring) and fdt.node in asg:
            asg[fdt.node].boost_python_export = False
    #if 'class ::boost::shared_ptr' in asg:
    #    for spc in asg['class ::boost::shared_ptr'].specializations(partial=False):
    #        spc.boost_python_export = False
    #if 'class ::std::smart_ptr' in asg:
    #    for spc in asg['class ::std::smart_ptr'].specializations(partial=False):
    #        spc.boost_python_export = False
    for tdf in asg.typedefs():
        if tdf.node in forbidden and not tdf.boost_python_export and tdf.type.target.boost_python_export:
            tdf.boost_python_export = True
            parent = tdf.parent
            while not parent.boost_python_export:
                parent.boost_python_export = True
                parent = parent.parent
        else:
            tdf.boost_python_export = False

def char_pointer(asg, filename, on_disk=True, **kwargs):
    prev = time.time()
    def is_char_pointer(proxy):
        return proxy.is_pointer and not proxy.nested.is_reference and not proxy.nested.is_pointer and isinstance(proxy.target, CharTypeProxy)
    def is_invalid_pointer(proxy):
        return proxy.nested.is_pointer or proxy.is_pointer and isinstance(proxy.target, FundamentalTypeProxy)
    if not isinstance(filename, basestring):
        raise TypeError('\'filename\' parameter')
    if filename in asg:
        modulenode = asg[filename]
    else:
        modulenode = asg.add_file(filename, proxy=kwargs.pop('module', BoostPythonModuleFileProxy))
    directory = modulenode.parent.globalname
    exportnode = modulenode.add_boost_python_export(directory + 'char_pointer_as_std_string.cpp', proxy=FileProxy)
    exportnode.content = ""
    functions = []
    for fct in asg.functions(pattern=kwargs.pop('pattern', None), free=None):
        if fct.boost_python_export and not fct.to_python:
            if is_char_pointer(fct.result_type) and not is_invalid_pointer(fct.resul_type) or any(is_char_pointer(prm.type) for prm in fct.parameters) and not any(is_invalid_pointer(prm.type) for prm in fct.parameters) and all(prm.localname for prm in fct.parameters):
                if isinstance(fct, MethodProxy):
                    parent = fct.parent
                    access = fct.access
                    while access == 'public' and hasattr(parent, 'access'):
                        access = parent.access
                        parent = parent.parent
                    if access == 'public':
                        functions.append(fct)
                else:
                    functions.append(fct)
    for fct in functions:
        rtype = fct.result_type
        if is_char_pointer(rtype):
            rtype = rtype.nested
            rtype._target = '::std::string'
        content = rtype.globalname + ' '
        content += 'char_pointer_to_std_string_' + fct.hash + '('
        if isinstance(fct, MethodProxy) and not fct.is_static:
            parent = fct.parent
            content += parent.globalname + ' const'*fct.is_const + ' * pointer_' + parent.hash + ', '
        for prm in fct.parameters:
            ptype = prm.type
            if is_char_pointer(ptype):
                ptype = ptype.nested
                ptype._target = '::std::string'
            content += ptype.globalname + ' ' + prm.localname +', '
        if content:
            content = content[:-2] + ')\n{\n'
            for prm in fct.parameters:
                ptype = prm.type
                if is_char_pointer(ptype):
                    content += '\t' + ptype.globalname + ' parameter_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::' + str(prm.index))).replace('-', '_') + ' = '
                    if ptype.nested.is_const:
                        content += prm.localname + '.c_str();\n'
                    else:
                        content += ' new char[' + prm.localname + '.length() + 1];\n'
                        content += '\t::std::strcpy(parameter_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::' + str(prm.index))).replace('-', '_') + ', ' + prm.localname + '.c_str());\n'
            rtype = fct.result_type
            if not isinstance(rtype.target, VoidTypeProxy):
                content += '\t' + rtype.globalname + ' result_'
                if is_char_pointer(rtype):
                    content += str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::char')).replace('-', '_')
                else:
                    content += str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname)).replace('-', '_')
                content += ' = '
            else:
                content += '\t'
            if isinstance(fct, MethodProxy) and not fct.is_static:
                content += 'pointer_' + fct.parent.hash + '->' + fct.localname
            else:
                content += fct.globalname
            content += '(' + ', '.join(prm.localname if not is_char_pointer(prm.type) else 'parameter_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::' + str(prm.index))).replace('-', '_') for prm in fct.parameters) + ');\n'
            for prm in fct.parameters:
                ptype = prm.type
                if is_char_pointer(ptype):
                    content += '\tdelete [] parameter_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::' + str(prm.index))).replace('-', '_') + ';\n'
            if not isinstance(rtype.target, VoidTypeProxy):
                if is_char_pointer(rtype):
                    rtype = rtype.nested
                    rtype._target = '::std::string'
                    content += '\t' + rtype.globalname + ' ' + ' result_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::std::string')).replace('-', '_') + '(result_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::char')).replace('-', '_') +');\n'
                    content += '\tdelete [] result_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::char')).replace('-', '_') + ';\n'
                    content += '\treturn result_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname + '::std::string')).replace('-', '_') +';\n'
                else:
                    content += '\treturn result_' + str(uuid.uuid5(uuid.NAMESPACE_X500, fct.globalname)).replace('-', '_').replace('-', '_') +';\n'
            content += '}\n'
            exportnode.content += '\n' + content
    content = ""
    for header in asg.headers(asg['::std::string'], *functions):
        if header.language == 'c':
            content += 'extern "C" { #include <' + asg.include_path(header) + '> }\n'
        else:
            content += '#include <' + asg.include_path(header) + '>\n'
    exportnode.content = content + '\n' + exportnode.content + '\n\nvoid char_pointer_as_std_string()\n{\n'
    for fct in functions:
        exportnode.content += '\tboost::python::def(char_pointer_as_std_string_' + fct.hash + ', char_pointer_as_std_string_' + fct.hash + ');\n'
    exportnode.content += '}'
    raise NotImplementedError() # TODO
    if on_disk:
        exportnode.write()
        modulenode.write()
    pydir = kwargs.pop('pydir', None)
    if kwargs.pop('python', True) and not pydir is None:
        asg.add_python_file(pydir=pydir, **kwargs)
    if kwargs.pop('sconscript', True) and not pydir is None:
        asg.add_sconsript(pydir=pydir, **kwargs)
    curr = time.time()
    diagnostic = BackEndDiagnostic()
    diagnostic.elapsed = curr - prev
    diagnostic._nodes = [modulenode, exportnode]
    return diagnostic