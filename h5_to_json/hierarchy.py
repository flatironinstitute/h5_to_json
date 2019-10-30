def hierarchy(X):
    nodes_by_alias = dict()
    groups = X.get('groups', {})
    for group in groups.values():
        aliases = group.get('alias', [])
        for alias0 in aliases:
            node = _find_or_create_node(nodes_by_alias, alias0)
            node['_attributes'] = _make_attributes(group.get('attributes', []))
    datasets = X.get('datasets', {})
    for dataset in datasets.values():
        aliases = dataset.get('alias', [])
        for alias0 in aliases:
            ind = alias0.rfind('/')
            if ind >= 0:
                parent_alias = alias0[:ind] or '/'
                name = alias0[ind + 1:]
                parent_node = _find_or_create_node(nodes_by_alias, parent_alias)
                if '_datasets' not in parent_node:
                    parent_node['_datasets'] = dict()
                dsnode = dict(
                    _attributes=_make_attributes(dataset.get('attributes', [])),
                )
                for key in ['type', 'shape', 'creationProperties', 'value', 'valueHash']:
                    if key in dataset:
                        dsnode[key] = dataset[key]
                parent_node['_datasets'][name] = dsnode
    return dict(
        root=nodes_by_alias.get('/', None)
    )

def _find_or_create_node(nodes_by_alias, alias):
    if alias in nodes_by_alias:
        return nodes_by_alias[alias]
    node = dict()
    nodes_by_alias[alias] = node
    if alias != '/':
        ind = alias.rfind('/')
        if ind >= 0:
            parent_alias = alias[:ind] or '/'
            name = alias[ind + 1:]
            parent_node = _find_or_create_node(nodes_by_alias, parent_alias)
            parent_node[name] = node
    return node

def _make_attributes(attributes_list):
    ret = dict()
    for a in attributes_list:
        ret[a['name']] = a
    return ret