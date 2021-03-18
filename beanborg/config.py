import yaml

class Config(object):
    def __init__(self, path=None, name=None, ref=None, target=None):
        self.path = path
        self.name = name
        self.ref = ref
        self.target = target
    
    def mover(loader, node):
	    values = loader.construct_mapping(node)
	    path = values["csv_path"]
	    name = values["csv_name"]
	    ref = values["bank_ref"]
	    target = values.get('csv_target', 'tmp')
	    return Config(path, name, ref, target)

if __name__ == '__main__':
	a = Config("a", "b", "c")

	print("path: %s, name: %s, ref: %s, target: %s"%(a.path, a.name, a.ref, a.target))

	a = Config.mover("pippo", "pluto", "paperino")

	print("path: %s, name: %s, ref: %s, target: %s"%(a.path, a.name, a.ref, a.target))
