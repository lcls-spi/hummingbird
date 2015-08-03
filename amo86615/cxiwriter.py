import h5py,os,numpy,time,sys

class CXIWriter:
    def __init__(self,filename,N,logger=None):
        self.filename = os.path.expandvars(filename)
        self.f = h5py.File(filename,"w")
        self.N = N
        self.logger = logger
    def write(self,d,prefix="",i=-1):
        for k in d.keys():
            name = prefix+"/"+k
            if self.logger is not None:
                self.logger.debug("Writing dataest %s",name)
            if isinstance(d[k],dict):
                if name not in self.f:
                    self.f.create_group(name)
                self.write(d[k],name,i)
            elif k != "i":
                self.write_to_dataset(name,d[k],d.get("i",i))
    def write_to_dataset(self,name,data,i):
        if self.logger is not None:
            self.logger.debug("Write dataset %s of event %i." % (name,i))
        if name not in self.f:
            #print name
            t0 = time.time()
            if numpy.isscalar(data):
                if i == -1:
                    s = [1]
                else:
                    s= [self.N]
                t=numpy.dtype(type(data))
                if t == "S":
                    t = h5py.new_vlen(str)
                axes = "experiment_identifier:value"
            else:
                data = numpy.array(data)
                s = list(data.shape)
                ndims = len(s)
                axes = "experiment_identifier"
                if ndims == 1: axes = axes + ":x"
                elif ndims == 2: axes = axes + ":y:x"
                elif ndims == 3: axes = axes + ":z:y:x"
                if i != -1:
                    s.insert(0,self.N)
                t=data.dtype
            self.f.create_dataset(name,s,t)
            self.f[name].attrs.modify("axes",[axes])
            t1 = time.time()
            if self.logger != None:
                self.logger.debug("Create dataset %s within %.1f sec.",name,t1-t0)

        if i == -1:
            if numpy.isscalar(data):
                self.f[name][0] = data
            else:
                self.f[name][:] = data[:]
        else:
            if numpy.isscalar(data):
                self.f[name][i] = data
            else:
                self.f[name][i,:] = data[:]
    def close(self):
        self.f.close()
