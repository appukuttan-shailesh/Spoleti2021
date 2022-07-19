import os
import sys
import numpy
import sciunit
import hippounit.capabilities as cap
from neuron import h


class ModelLoader(sciunit.Model,
                  cap.ReceivesSquareCurrent_ProvidesResponse):

    def __init__(self, name="Tg_3m", hoc_path=None, template_name=None, mod_files_path=None):
        """ Constructor. """
        # ModelLoader(hoc_path="./modeldb_ventralAD/cell_seed2_0.hoc", template_name="test_Wt", mod_files_path="./modeldb_ventralAD")

        """ This class should be used with Jupyter notebooks"""
        self.name = name
        sciunit.Model.__init__(self, name=name)

        self.mod_files_path = mod_files_path
        self.libpath = 'x86_64/.libs/libnrnmech.so'
        self.hoc_path = hoc_path
        self.template_name = template_name
        self.base_directory = './validation_results/'   # inside current directory

        self.soma = None # remove?
        self.SomaSecList_name = "somatic"
        self.v_init = -70
        self.celsius = 25

        self.cvode_active = False

        self.compile_mod_files()

    def compile_mod_files(self):
        if self.mod_files_path is None:
            raise Exception(
                "Please give the path to the mod files (eg. mod_files_path = \'/home/models/CA1_pyr/mechanisms/\') as an argument to the ModelLoader class")
        if os.path.isfile(os.path.join(self.mod_files_path, self.libpath)) is False:
            os.system("cd " + "\'" + self.mod_files_path +
                      "\'" + "; nrnivmodl")

    def translate(self, sectiontype, distance=0):
        if "soma" in sectiontype:
            return self.soma
        else:
            return sectiontype


    def load_mod_files(self):
        # print(os.path.join(self.mod_files_path, self.libpath))
        print(os.path.join(self.mod_files_path, self.libpath))
        status = h.nrn_load_dll(os.path.join(self.mod_files_path, self.libpath))
        print("nrn_load_dll: {}".format("success" if status==1 else "fail"))

    def initialise(self):

        save_stdout = sys.stdout  # To supress hoc output from Jupyter notebook
        # sys.stdout = open('/dev/null', 'a')  # not showing it
        self.load_mod_files()

        if self.hoc_path is None:
            raise Exception(
                "Please give the path to the hoc file (eg. model.modelpath = \"/home/models/CA1_pyr/CA1_pyr_model.hoc\")")

        status = h.load_file("stdrun.hoc")
        print("loading stdrun.hoc: {}".format("success" if status==1 else "fail"))
        status = h.load_file(str(self.hoc_path))
        print("loading hoc_path = {}: {}".format(str(self.hoc_path), "success" if status==1 else "fail"))

        if self.soma is None and self.SomaSecList_name is None:
            raise Exception(
                "Please give the name of the soma (eg. model.soma=\"soma[0]\"), or the name of the somatic section list (eg. model.SomaSecList_name=\"somatic\")")

        try:
            if self.template_name is not None and self.SomaSecList_name is not None:

                h('objref testcell')
                h('testcell = new ' + self.template_name + '("./modeldb_ventralAD/morphology", "062817C_B.swc")')

                exec('self.soma_ = h.testcell.' + self.SomaSecList_name)

                for s in self.soma_:
                    self.soma = h.secname()

            elif self.template_name is not None and self.SomaSecList_name is None:
                h('objref testcell')
                h('testcell = new ' + self.template_name)
                # in this case self.soma is set in the jupyter notebook
            elif self.template_name is None and self.SomaSecList_name is not None:
                exec('self.soma_ = h.' + self.SomaSecList_name)
                for s in self.soma_:
                    self.soma = h.secname()
            # if both is None, the model is loaded, self.soma will be used
        except AttributeError:
            print("The provided model template is not accurate. Please verify!")
        except Exception:
            print("If a model template is used, please give the name of the template to be instantiated (with parameters, if any). Eg. model.template_name=CCell(\"morph_path\")")
            raise
        sys.stdout = save_stdout  # setting output back to normal

    def inject_current(self, amp, delay, dur, section_stim, loc_stim, section_rec, loc_rec):
        self.initialise()

        if self.cvode_active:
            h.cvode_active(1)
        else:
            h.cvode_active(0)

        stim_section_name = self.translate(section_stim, distance=0)
        rec_section_name = self.translate(section_rec, distance=0)

        exec("self.sect_loc_stim=h." +
             str(stim_section_name)+"("+str(loc_stim)+")")

        print("- running amplitude: " + str(amp) + " on model: " +
              self.name + " at: " + stim_section_name + "(" + str(loc_stim) + ")")

        self.stim = h.IClamp(self.sect_loc_stim)

        self.stim.amp = amp
        self.stim.delay = delay
        self.stim.dur = dur

        exec("self.sect_loc_rec=h." + str(rec_section_name)+"("+str(loc_rec)+")")

        rec_t = h.Vector()
        rec_t.record(h._ref_t)

        rec_v = h.Vector()
        rec_v.record(self.sect_loc_rec._ref_v)

        h.stdinit()

        dt = 0.025
        h.dt = dt
        h.steps_per_ms = 1/dt
        h.v_init = self.v_init

        h.celsius = self.celsius
        h.init()
        h.tstop = delay + dur + 200
        h.run()

        t = numpy.array(rec_t)
        v = numpy.array(rec_v)

        return t, v
