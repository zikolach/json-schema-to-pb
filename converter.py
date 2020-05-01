#!/usr/bin/env python3
import json
import logging
import click

logging.basicConfig()
log = logging.getLogger()


def ref_name(ref):
    return ref[len('#/definitions/'):]


def cap(name):
    return f'{name[:1].upper()}{name[1:]}'


def resolve(element):
    while '$ref' in element.keys():
        ref = element['$ref']
        name = ref_name(ref)
        element = schema['definitions'][name]
    return element


def merge(element):
    while 'allOf' in element.keys():
        element = {**element}
        all_of = element['allOf']
        del element['allOf']
        for part in all_of:
            if '$ref' in part.keys():
                part = resolve(part)
            if 'type' in part.keys() and 'type' not in element.keys():
                element['type'] = part['type']
            if 'properties' in part.keys():
                if 'properties' not in element.keys():
                    element['properties'] = {}
                element['properties'] = {**element['properties'],
                                         **part['properties']}
            if 'allOf' in part.keys():
                if 'allOf' not in element.keys():
                    element['allOf'] = []
                element['allOf'].extend(part['allOf'])
    return element


class TypedProperty:
    def __init__(self, name, prop_type, repeated):
        self.name = name
        self.type = prop_type
        self.repeated = repeated

    def print(self, printer, indent=0, index=1):
        prefix = '  '*indent
        printer.print(f'{prefix}{"repeated " if self.repeated else ""}'
                      f'{self.type} {self.name} = {index};')


class StringProperty(TypedProperty):
    def __init__(self, name, repeated):
        super().__init__(name, 'string', repeated)


class DoubleProperty(TypedProperty):
    def __init__(self, name, repeated):
        super().__init__(name, 'double', repeated)


class BoolProperty(TypedProperty):
    def __init__(self, name, repeated):
        super().__init__(name, 'bool', repeated)


class Int32Property(TypedProperty):
    def __init__(self, name, repeated):
        super().__init__(name, 'int32', repeated)


class MapProperty(TypedProperty):
    def __init__(self, name, key, value):
        super().__init__(name, f'map<{key}, {value}>', repeated=False)


class Enum:
    def __init__(self, name, element):
        self.name = name
        self.values = element['enum']

    def print(self, printer, indent=0):
        prefix = '  '*indent
        printer.print(f'{prefix}enum {self.name} {{')
        for index, value in enumerate(self.values):
            printer.print(f'{prefix}  {value} = {index};')
        printer.print(f'{prefix}}}\n')


class Message:
    def __init__(self, name, element, chain):
        self.name = name
        self.properties = []
        self.subtypes = []

        if 'properties' in element.keys():
            for prop_name, prop_element in element['properties'].items():
                if '$ref' in prop_element.keys():
                    prop_element = resolve(prop_element)
                if 'type' in prop_element.keys():
                    prop_type = prop_element['type']
                    repeated = False
                    if prop_type == 'array':
                        repeated = True
                        prop_element = prop_element['items']
                        if '$ref' in prop_element.keys():
                            prop_element = resolve(prop_element)
                        if 'allOf' in prop_element.keys():
                            prop_element = merge(prop_element)
                        if 'type' in prop_element.keys():
                            prop_type = prop_element['type']
                        else:
                            log.warning(f'Cannot process {prop_name}')
                            continue

                    if prop_type == 'object':
                        if 'patternProperties' in prop_element.keys():
                            map_prop = MapProperty(prop_name,
                                                   'string', 'string')
                            self.properties.append(map_prop)
                        else:
                            subtype_name = cap(prop_name)
                            if subtype_name not in chain:
                                log.info(f'Add {subtype_name} to {chain}')
                                subtype = Message(subtype_name, prop_element,
                                                  chain + [subtype_name])
                                self.subtypes.append(subtype)
                            else:
                                log.info(f'Cyclic reference [{subtype_name}] '
                                         f'is already in {"->".join(chain)} ')
                            typed_prop = TypedProperty(prop_name,
                                                       cap(prop_name),
                                                       repeated)
                            self.properties.append(typed_prop)
                    elif prop_type == 'string':
                        if 'enum' in prop_element.keys():
                            enum = Enum(cap(prop_name), prop_element)
                            self.subtypes.append(enum)
                            typed_prop = TypedProperty(prop_name,
                                                       cap(prop_name),
                                                       repeated)
                            self.properties.append(typed_prop)
                        else:
                            string_prop = StringProperty(prop_name, repeated)
                            self.properties.append(string_prop)
                    elif prop_type == 'number':
                        double_prop = DoubleProperty(prop_name, repeated)
                        self.properties.append(double_prop)
                    elif prop_type == 'integer':
                        int_prop = Int32Property(prop_name, repeated)
                        self.properties.append(int_prop)
                    elif prop_type == 'boolean':
                        bool_prop = BoolProperty(prop_name, repeated)
                        self.properties.append(bool_prop)
                    else:
                        log.warning(f'Unrecognized {prop_type} '
                                    f'for {prop_name}')

    def print(self, printer, indent=0):
        if indent == 0:
            printer.print('syntax = "proto3";\n')
        prefix = '  '*indent
        printer.print(f'{prefix}message {self.name} {{')
        for subtype in self.subtypes:
            subtype.print(printer, indent+1)
        for index, prop in enumerate(self.properties):
            prop.print(printer, indent+1, index+1)
        printer.print(f'{prefix}}}\n')


class Printer:
    def print(self, text):
        print(text)


class FilePrinter(Printer):
    def __init__(self, output):
        self.file = output

    def __del__(self):
        if self.file:
            self.file.close()

    def print(self, text):
        self.file.write(f"{text}\n")


schema = {}


@click.command()
@click.argument('schema_file', type=click.File('r'))
@click.argument('output', default='output/generated.proto',
                type=click.File('w'))
@click.option('--root-name', type=str, default='Envelope',
              help='Name of root message type')
@click.option('--verbose', is_flag=True)
def main(schema_file, output, root_name, verbose):
    if verbose:
        log.setLevel('DEBUG')
    global schema
    schema = json.load(schema_file)
    proto = Message(root_name, schema, [])
    proto.print(FilePrinter(output))


if __name__ == '__main__':
    main()
