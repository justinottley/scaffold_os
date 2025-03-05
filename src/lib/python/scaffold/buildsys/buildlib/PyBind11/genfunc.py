

class Return:

    def __init__(self, method):
        self.method = method

    def gen(self):
        return self.method.gen_call_sig()


class QStringReturn(Return):


    def gen(self):

        result = '{}.toStdString()'.format(
            self.method.gen_call_sig()
        )

        return result


class QVariantMapReturn(Return):

    def gen(self):
        result = 'PyQVariantMap({}).toDict()'.format(
            self.method.gen_call_sig()
        )
        return result


class QVariantListReturn(Return):

    def gen(self):
        result = 'PyQVariant({}).toPyList()'.format(
            self.method.gen_call_sig()
        )
        return result


class QStringListReturn(Return):

    def gen(self):
        result = 'PyQVariant({}).toPyList()'.format(
            self.method.gen_call_sig()
        )
        return result


class QVariantReturn(Return):

    def gen(self):
        result = 'PyQVariant({}).pyval()'.format(
            self.method.gen_call_sig()
        )
        return result


class Param:

    def __init__(self, ptype):
        self.ptype = ptype

    def gen_type(self):
        return self.ptype

    def gen_conv(self, arg):
        return arg


class QStringParam(Param):

    def gen_type(self):
        return 'py::str'

    def gen_conv(self, arg):
        return 'QString(std::string({}).c_str())'.format(arg)


class QVariantMapParam(Param):

    def gen_type(self):
        return 'py::dict'

    def gen_conv(self, arg):
        return 'PyQVariantMap({}).val()'.format(arg)


class QVariantListParam(Param):

    def gen_type(self):
        return 'py::list'

    def gen_conv(self, arg):
        return 'PyQVariant({}).toList()'.format(arg)


class QStringListParam(Param):

    def gen_type(self):
        return 'py::list'

    def gen_conv(self, arg):
        return 'PyQVariant({}).toStringList()'.format(arg)


class QVariantParam(Param):

    def gen_type(self):
        return 'py::object'

    def gen_conv(self, arg):
        return 'PyQVariant::fromPyHandle({})'.format(arg)


class Method:

    RETURN_HANDLERS = {
        'QString': QStringReturn,
        'QVariantMap': QVariantMapReturn,
        'QVariantList': QVariantListReturn,
        'QStringList': QStringListReturn,
        'QVariant': QVariantReturn
    }

    PARAM_HANDLERS = {
        'QString': QStringParam,
        'QVariantMap': QVariantMapParam,
        'QVariantList': QVariantListParam,
        'QStringList': QStringListParam,
        'QVariant': QVariantParam
    }


    def __init__(self, class_name, slot_info, pb_slot_info):
        self.class_name = class_name
        self.slot_info = slot_info
        self.pb_slot_info = pb_slot_info


    @property
    def return_type(self):
        return self.slot_info['returnType']

    @property
    def needs_wrapper(self):

        if self.slot_info['returnType'] in self.RETURN_HANDLERS:
            return True


        for arg in self.slot_info.get('arguments', []):
            if arg['type'] in self.PARAM_HANDLERS:
                return True


    @property
    def is_constructor(self):
        cname = 'new_{}'.format(self.class_name)
        return cname == self.slot_info['name']


    @staticmethod
    def make(class_name, slot_entry, pb_slot_info):

        if slot_entry['name'] == 'new_{}'.format(class_name):
            return ConstructorMethod(class_name, slot_entry, pb_slot_info)

        return Method(class_name, slot_entry, pb_slot_info)


    def return_handler(self):

        if self.return_type in self.RETURN_HANDLERS:
            r_cls = self.RETURN_HANDLERS[self.return_type]

            return r_cls(self)

        return Return(self)


    def param_handler(self, ptype):

        if ptype in self.PARAM_HANDLERS:
            p_cls = self.PARAM_HANDLERS[ptype]
            return p_cls(ptype)

        return Param(ptype)


    def gen_def_sig_args(self):

        arg_lines = []
        arg_count = 0
        for arg in self.slot_info.get('arguments', []):

            ph = self.param_handler(arg['type'])
            type_str = ph.gen_type()


            arg_lines.append('{} arg{}'.format(type_str, arg_count))
            arg_count += 1

        arg_str = ', '.join(arg_lines)
        return arg_str


    def gen_def_sig(self):

        arg_str = self.gen_def_sig_args()
        if arg_str:
            result = '[]({}& pcls, {})'.format(self.class_name, arg_str)

        else:
            result = '[]({}& pcls)'.format(self.class_name)


        return result


    def gen_arg_str(self):

        result_lines = []

        arg_count = 0
        for arg in self.slot_info.get('arguments', []):

            arg_name = 'arg{}'.format(arg_count)
            ph = self.param_handler(arg['type'])

            arg_code = ph.gen_conv(arg_name)
    
            result_lines.append(arg_code)
            arg_count += 1

        return ', '.join(result_lines)


    def gen_call_sig(self):

        arg_str = self.gen_arg_str()
        result = 'pcls.{}({})'.format(
            self.slot_info['name'], arg_str
        )

        return result


    def gen_wrapper(self):

        result  = '    .def("{}",\n'.format(self.slot_info['name'])
        result += '      {}\n'.format(self.gen_def_sig())
        result += '        {\n'
        result += '           return {};\n'.format(self.return_handler().gen())
        result += '        }'

        return result


    def gen_simple(self):

        result = '    .def("{}", &{}::{}'.format(
            self.slot_info['name'],
            self.class_name,
            self.slot_info['name']
        )

        return result


    def gen(self):

        nw = self.needs_wrapper
        if nw:
            result = self.gen_wrapper()
        else:
            result = self.gen_simple()

        retval_policy = self.pb_slot_info.get('retval_policy')
        if '*' in self.slot_info['returnType']:
            retval_policy = 'reference'

        if retval_policy:
            result += ',\n      py::return_value_policy::{})\n'.format(retval_policy)

        else:
            if nw:
                result += '\n    )\n'
            else:
                result += ')\n'

        return result



class ConstructorMethod(Method):

    def gen_def_sig(self):

        arg_str = self.gen_def_sig_args()
        result = '[]({})'.format(arg_str)

        return result


    def gen_call_sig(self):

        arg_str = self.gen_arg_str()
        result = '{}::{}({})'.format(
            self.class_name,
            self.slot_info['name'],
            arg_str
        )
        return result


    def gen_wrapper(self):

        result  = '    .def(py::init(\n'
        result += '      {}\n'.format(self.gen_def_sig())
        result += '        {\n'
        result += '           return {};\n'.format(self.return_handler().gen())
        result += '        })'

        return result


    def gen_simple(self):

        result = '   .def(py::init(&{}::{})'.format(
            self.class_name,
            self.slot_info['name']
        )
        return result