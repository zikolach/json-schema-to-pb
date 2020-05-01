# JSON Schema to Protocol Buffers converter

This repository is an attempt to create a converter from [JSON Schema](https://json-schema.org/) format to [Protocol Buffers](https://developers.google.com/protocol-buffers) definitions.  
It is supposed to provide schema-compatible JSON output serializing data using generated Protocol Buffers API.

## Getting started

To install necessary dependencies you can use [virtualenv](https://virtualenv.pypa.io/en/latest/) utility

```
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

To convert your JSON schema file to Protocol Buffers definition file run `converter.py`, e.g.:

```
$ ./converter.py schemes/example.json
```

By default, it will create file `output/generated.proto` in the current directory.

To compile proto file into language-specific API use `protoc` compiler, e.g.

```
$ protoc --python_out=. output/generated.proto
```

```
$ touch output/__init__.py
$ python
Python 3.7.7 (default, Mar 10 2020, 15:43:33) 
[Clang 11.0.0 (clang-1100.0.33.17)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import output.generated_pb2 as pb
>>> from google.protobuf.json_format import MessageToJson, Parse
>>> source = """{
...   "checked": false,
...   "dimensions": {
...     "width": 5,
...     "height": 10
...   },
...   "id": 1,
...   "name": "A green door",
...   "price": 12.5,
...   "tags": [
...     "home",
...     "green"
...   ]
... }"""
>>> message = Parse(source, pb.Envelope())
>>> out = MessageToJson(message)
>>> print(out)
{
  "dimensions": {
    "width": 5,
    "height": 10
  },
  "id": 1,
  "name": "A green door",
  "price": 12.5,
  "tags": [
    "home",
    "green"
  ]
}
>>>
```

## Caveats

The current version of converter supports very limited number of features of JSON schema and Protocol Buffers.

