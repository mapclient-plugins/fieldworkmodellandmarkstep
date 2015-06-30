
'''
MAP Client Plugin Step
'''
import os

from PySide import QtGui
from PySide import QtCore

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
# fromapclientplugins.m fieldworkmodellandmarkstep.configuredialog import ConfigureDialog

from gias.musculoskeletal import fw_pelvis_model_data as pcd
from gias.musculoskeletal import fw_pelvis_measurements as pm
from gias.musculoskeletal import fw_femur_model_data as fcd
from gias.musculoskeletal import fw_femur_measurements as fm
from fieldwork.field import geometric_field

class fieldworkmodellandmarkStep(WorkflowStepMountPoint):
    '''
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    '''
    _validModelNames = ('left hemi-pelvis', 'right hemi-pelvis', 'sacrum', 'right femur', 'left femur')

    def __init__(self, location):
        super(fieldworkmodellandmarkStep, self).__init__('Fieldwork Model Landmarker', location)
        self._configured = True # A step cannot be executed until it has been configured.
        self._category = 'Anthropometry'
        # Add any other initialisation code here:
        self._icon = QtGui.QImage(':/fieldworkmodellandmarkstep/images/fieldworkmodellandmarkicon.png')
        # Ports:
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'ju#fieldworkmodeldict'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#landmarks'))
        self._config = {}
        self._config['identifier'] = ''
        self._landmarks = {}
        self._models = None

    def execute(self):
        '''
        Add your code here that will kick off the execution of the step.
        Make sure you call the _doneExecution() method when finished.  This method
        may be connected up to a button in a widget for example.
        '''
        # Put your execute step code here before calling the '_doneExecution' method.
        modelNames = self._models.keys()
        if 'right femur' in modelNames:
            self._getRightFemurLandmarks()

        if 'left femur' in modelNames:
            self._getLeftFemurLandmarks()
        
        if 'pelvis' in modelNames:
            self._getWholePelvisLandmarks()
        elif ('right hemi-pelvis' in modelNames) and\
             ('left hemi-pelvis' in modelNames) and\
             ('sacrum' in modelNames):
            self._getPelvisLandmarks()
        
        self._printLandmarks()
        self._doneExecution()

    def _printLandmarks(self):
        print('Landmarks Evaluated:')
        landmarkNames = sorted(self._landmarks.keys())
        for ldn in landmarkNames:
            print('{}: {:6.2f}, {:6.2f}, {:6.2f}'.format(
                    ldn,
                    self._landmarks[ldn][0], 
                    self._landmarks[ldn][1], 
                    self._landmarks[ldn][2], 
                    ))

    def _getRightFemurLandmarks(self):
        femurM = fm.FemurMeasurements(self._models['right femur'])
        femurM.calcHeadDiameter()
        femurM.calcEpicondylarWidthByNode()
        femurLandmarks = {}
        femurLandmarks['RFHC'] = femurM.measurements['head_diameter'].centre
        femurLandmarks['RMEC'] = femurM.measurements['epicondylar_width'].p2[1]
        femurLandmarks['RLEC'] = femurM.measurements['epicondylar_width'].p1[1]
        self._landmarks.update(femurLandmarks)

    def _getLeftFemurLandmarks(self):
        femurM = fm.FemurMeasurements(self._models['left femur'])
        femurM.calcHeadDiameter()
        femurM.calcEpicondylarWidthByNode()
        femurLandmarks = {}
        femurLandmarks['LFHC'] = femurM.measurements['head_diameter'].centre
        femurLandmarks['LMEC'] = femurM.measurements['epicondylar_width'].p2[1]
        femurLandmarks['LLEC'] = femurM.measurements['epicondylar_width'].p1[1]
        self._landmarks.update(femurLandmarks)

    def _getWholePelvisLandmarks(self):
        pelvisM = pm.PelvisMeasurements(self._models['pelvis'])
        pelvisM.calcAcetabulumDiameters()
        self._landmarks.update(pelvisM.measurements['landmarks_unaligned'].value)
        # self._landmarks['PS'] = (self._landmarks['LSP'] + self._landmarks['RSP'])/2.0

    def _getPelvisLandmarks(self):
        combPelvisGF = geometric_field.geometric_field(
                        'combined pelvis', 3, field_dimensions=2,
                        field_basis={'tri10':'simplex_L3_L3','quad44':'quad_L3_L3'})
        combPelvisGF.ensemble_field_function.name = 'pelvis_combined_cubic'
        combPelvisGF.ensemble_field_function.mesh.name = 'pelvis_combined_cubic'
        combPelvisGF.add_element_with_parameters(
                        self._models['right hemi-pelvis'].ensemble_field_function,
                        self._models['right hemi-pelvis'].get_field_parameters(),
                        tol=0 )
        combPelvisGF.add_element_with_parameters(
                        self._models['left hemi-pelvis'].ensemble_field_function,
                        self._models['left hemi-pelvis'].get_field_parameters(),
                        tol=0 )
        combPelvisGF.add_element_with_parameters(
                        self._models['sacrum'].ensemble_field_function,
                        self._models['sacrum'].get_field_parameters(),
                        tol=0 )

        pelvisM = pm.PelvisMeasurements(combPelvisGF)
        self._landmarks.update(pelvisM.measurements['landmarks_unaligned'].value)
        # self._landmarks['PS'] = (self._landmarks['LSP'] + self._landmarks['RSP'])/2.0

    def setPortData(self, index, dataIn):
        '''
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.
        '''
        self._models = dataIn # ju#fieldworkmodeldict

    def getPortData(self, index):
        '''
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.
        '''
        return self._landmarks # ju#landmarks

    def configure(self):
        '''
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        '''

        self._configured = True

        # dlg = ConfigureDialog()
        # dlg.identifierOccursCount = self._identifierOccursCount
        # dlg.setConfig(self._config)
        # dlg.validate()
        # dlg.setModal(True)
        
        # if dlg.exec_():
        #     self._config = dlg.getConfig()
        
        # self._configured = dlg.validate()
        # self._configuredObserver()

    def getIdentifier(self):
        '''
        The identifier is a string that must be unique within a workflow.
        '''
        return self._config['identifier']

    def setIdentifier(self, identifier):
        '''
        The framework will set the identifier for this step when it is loaded.
        '''
        self._config['identifier'] = identifier

    def serialize(self, location):
        '''
        Add code to serialize this step to disk.  The filename should
        use the step identifier (received from getIdentifier()) to keep it
        unique within the workflow.  The suggested name for the file on
        disk is:
            filename = getIdentifier() + '.conf'
        '''
        pass
        # configuration_file = os.path.join(location, self.getIdentifier() + '.conf')
        # conf = QtCore.QSettings(configuration_file, QtCore.QSettings.IniFormat)
        # conf.beginGroup('config')
        # conf.setValue('identifier', self._config['identifier'])
        # conf.endGroup()


    def deserialize(self, location):
        '''
        Add code to deserialize this step from disk.  As with the serialize 
        method the filename should use the step identifier.  Obviously the 
        filename used here should be the same as the one used by the
        serialize method.
        '''
        pass
        # configuration_file = os.path.join(location, self.getIdentifier() + '.conf')
        # conf = QtCore.QSettings(configuration_file, QtCore.QSettings.IniFormat)
        # conf.beginGroup('config')
        # self._config['identifier'] = conf.value('identifier', '')
        # conf.endGroup()

        # d = ConfigureDialog()
        # d.identifierOccursCount = self._identifierOccursCount
        # d.setConfig(self._config)
        # self._configured = d.validate()


