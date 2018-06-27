'''
Test
'''
import json
import re

modules = {}
classes = {}
searches = []
skipped = []
# Constructor, Accessor, Property, Method
# inheritedFrom, implementedTypes

def searchable( key, name, kind ):
  searches.append( [key, name, kind] )

def clean_quoted( n ):
  return re.sub(r'\"', '', n)

def get_source( sources ):
  return [ [ s['fileName'], s['line'], s['character'] ] for s in sources ] 

def props_module( m ):
  return {  
    'name': clean_quoted( m['name'] ), 
    'source': get_source( m['sources'] ), 
    'kind': 'Module',
    'id': m['id'],
    'comment': get_comment( m ),
    'classes': []
  }


def props_class( c ):
  return {  
    'name': c['name'],
    'source': get_source( c['sources'] ), 
    'kind': c['kindString'],
    'id': c['id'],
    'comment': get_comment( c ),
    'constructor': [],
    'accessors': [],
    'methods': [],
    'variables': [],
    'properties': [],
    'flags': get_flags( c ),
    'extends': [ im.get('name', "") for im in c.get('extendedTypes', []) ],
    'implements': [ im.get('name', "") for im in c.get('implementedTypes', []) ]
  }




def parse_modules():
   
  with open('docs.json') as file:
    data = json.load(file)
    _mds = [d for d in data['children']]
    # module_names = [d['name'] for d in modules]

    for m in _mds:
      name = clean_quoted(m['name'])

      if not name[0] == "_":
        modules[name] = props_module( m )
        modules[name]['classes'] = parse_classes( m, name )
        searchable( name, name, "Module" )

      else:
        skipped.append( "Module."+name )

    for c in classes:
      save_class( classes[c], c )

    # save_temp(json.dumps(searches, indent=2))
    # save_temp( json.dumps([classes['Pt.Pt']], indent=2 ))
    # save_temp(json.dumps(modules['Bound']['children'][0], indent=2, sort_keys=True))

    # print( skipped )



def parse_classes( mod, mod_name ):
  
  if  not 'children' in mod: 
    return []

  _cls = [d for d in mod['children']]
  names = []
  for c in _cls:

    if c['kindString'] != 'Variable' and not_private( c['name'] ) :

      fullname =f"{mod_name}_{c['name']}"
      classes[ fullname ] = props_class( c )

      parse_class_children( classes[ fullname ], c )
      names.append( c['name'] )
      searchable( fullname, c['name'], c['kindString'] )

    else:
      skipped.append( f"{mod_name}_{c['name']}" )
    
  return names



def parse_class_children( c, orig_c ):

  for ch in orig_c.get('children', []):
    if not_private( ch['name'] ):

      k = ch['kindString']
      if k == "Method":
        c['methods'].append( parse_class_method( ch ) )

      elif k == "Accessor":
        c['accessors'].append( parse_class_accessor( ch ) )

      elif k == "Variable":
        c['variables'].append( parse_class_variable( ch ) )

      elif k == "Property":
        c['properties'].append( parse_class_property( ch ) )

      elif k == "Constructor":
        c['constructor'].append( parse_class_method( ch ) )

      else:
        skipped.append( f"{c['name']}.{ch['name']}" )
    else:
      skipped.append( f"{c['name']}.{ch['name']}" )



def parse_class_accessor( c ):

  if not c.get('name', False): 
    return {}

  getters = [parse_accessor_signature(s) for s in c.get('getSignature', [])]
  setters = [parse_accessor_signature(s) for s in c.get('setSignature', [])]

  return {
    'name': c['name'],
    'source': get_source( c.get('sources', []) ), 
    'id': c['id'],
    'flags': get_flags( c ),
    'overrides': c.get('overwrites', {}).get('name', False),
    'inherits': c.get('inheritedFrom', {}).get('name', False),
    'comment': get_comment( c ),
    'getter': False if not getters else getters[0],
    'setter': False if not setters else setters[0]
  }


def parse_accessor_signature( c ):
  if not c: 
    return False

  acc = { 'type': c.get('type',{}).get('name', "") } 
  if c.get('parameters', False):
    acc['parameters'] = parse_class_method_param( c['parameters'][0] ) if c['parameters'] else {}
  return acc



def parse_class_variable( c ):
  if not c.get('name', False): 
    return False

  return {
    'name': c['name'],
    'source': get_source( c.get('sources', []) ), 
    'id': c['id'],
    'flags': get_flags( c ),
    'type': get_type( c ),
    'overrides': c.get('overwrites', {}).get('name', False),
    'inherits': c.get('inheritedFrom', {}).get('name', False),
    'comment': get_comment( c )
  }


def parse_class_property( c ):
  if not c.get('name', False): 
    return False

  return {
    'name': c['name'],
    'source': get_source( c.get('sources', []) ), 
    'id': c['id'],
    'flags': get_flags( c ),
    'type': get_type( c ),
    'overrides': c.get('overwrites', {}).get('name', False),
    'inherits': c.get('inheritedFrom', {}).get('name', False),
    'comment': get_comment( c )
  }


def parse_class_method( c ):
  if not c.get('name', False): 
    return {}

  return {
    'name': c['name'],
    'source': get_source( c.get('sources', []) ), 
    'id': c['id'],
    'flags': get_flags( c ),
    'overrides': c.get('overwrites', {}).get('name', False),
    'inherits': c.get('inheritedFrom', {}).get('name', False),
    'signatures': [ parse_class_method_signature( s ) for s in c.get('signatures', {}) ]
  }


def parse_class_method_signature( c ):
  return {
    'comment': get_comment( c ) ,
    'returns': get_type( c.get('type', {}) ),
    'parameters': [ parse_class_method_param(p) for p in c.get('parameters', []) ]
  }


def parse_class_method_param( c ):
  if not c.get('name', False): 
    return {}

  return {
    'name': c['name'],
    'comment': get_comment( c ),
    'type': get_type( c.get("type", {'name': 'any?'}) ),
    'default': c.get('defaultValue', False)
  }


def save_toc():
  toc = {}
  for key in classes:
    c = key.split("_")

    if c[0] in toc:
      toc[ c[0] ].append( c[1] )
    else:
      toc[ c[0] ] = [ c[1] ]

  f = open('modules.json', 'w')
  f.write( json.dumps( toc, indent=2 ) )
  f.close()

def save_class(data, name):
  f = open(f'{name}.json', 'w')
  f.write( json.dumps( data, indent=2 ) )
  f.close()


def save_temp(data):
  f = open('temp.json', 'w')
  f.write(data)
  f.close()




def get_comment( c ):
  return c.get('comment', {}).get('shortText', False) or c.get('comment', {}).get('text', "")

def get_type( c, pre="", post="" ):
  ts = ""
  try:
    if 'name' in c:
      n = c['name']
      return f"{pre}{n}{post}"
    else:

      # union
      if 'types' in c:
        return " | ".join( [get_type( _t, pre, post ) for _t in c['types']] )
      elif 'elements' in c:
        return ",".join( [get_type( _t, pre, post ) for _t in c['elements']] )
      elif 'elementType' in c:
        ct = c.get('type', "")
        ct = "[]" if ct == "array" else ct
        return get_type( c['elementType'], pre, f"{post}{ct}" )
      elif 'declaration' in c:
        sig = c['declaration'].get('signatures', [])
        params = sig[0].get("parameters")
        pp = [] 
        for p in params:
          _n = p.get("name", "")
          if _n != "this" and _n != "Z":
            _t = get_type( p.get("type", {} ), f'{pre}{_n}:' )
            pp.append( _t )
        
        # ( [get_type( p.get("type", {} ), f'{pre}{p.get("name", "")}:', post ) for p in params if p.get("name") != "this" ] )
        fn = f'{c.get("name", "")} {"Fn" if pp else ""}({", ".join( pp )})'
        return fn
        # get_type( c['declaration'].get('parameters', {}).get('type', {}), "function" )
      else:
        return get_type( c.get("type", ""), pre, post )

  except BaseException:
    # print( c, pre )
    return ""

  return ts

  # if 'type' in c:
  #   t = c['type']
    
  #   if 'types' in t:
  #     ts += ",".join( [get_type( _t, pre ) for _t in t['types']] )
  #   elif 'declaration' in t:
  #     get_type( t['declaration'].get('parameters', {}).get('type', {}), "function" )
  #   elif 'name' in t:
  #     # n = t if isinstance( t, str ) else t.get("name", "###")
  #     # if pre:
  #     #   print( n, pre, "!!!" )
  #     ts = f"{pre}<{t['name']}>" if pre else t['name']

  # elif 'elementType' in c:
  #     get_type( c['elementType'], pre )
        
          
  
  return ts


def not_private( n ):
  return n[0] != "_"

def get_flags( c ):
  f = c.get('flags', {})
  f.pop( "isExported", None )
  return f


parse_modules()
save_toc()
