'''
MAP Client Plugin Step
'''
from PySide6 import QtGui

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint

from gias3.musculoskeletal import fw_pelvis_measurements as pm
from gias3.musculoskeletal import fw_model_landmarks as fml
from gias3.fieldwork.field import geometric_field

FEMUR_LANDMARKS = {'FHC': 'femur-HC',
                   'MEC': 'femur-MEC',
                   'LEC': 'femur-LEC',
                   'FGT': 'femur-GT',
                   'kneecentre': 'femur-kneecentre',
                   }

PELVIS_LANDMARKS = {'LASIS': 'pelvis-LASIS',
                    'RASIS': 'pelvis-RASIS',
                    'LPSIS': 'pelvis-LPSIS',
                    'RPSIS': 'pelvis-RPSIS',
                    'Sacral': 'pelvis-Sacral',
                    'LHJC': 'pelvis-LHJC',
                    'RHJC': 'pelvis-RHJC',
                    }


class fieldworkmodellandmarkStep(WorkflowStepMountPoint):
    '''
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    '''
    _validModelNames = ('left hemi-pelvis', 'right hemi-pelvis', 'sacrum', 'right femur', 'left femur')

    def __init__(self, location):
        super(fieldworkmodellandmarkStep, self).__init__('Fieldwork Model Landmarker', location)
        self._configured = True  # A step cannot be executed until it has been configured.
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
        elif ('right hemi-pelvis' in modelNames) and \
                ('left hemi-pelvis' in modelNames) and \
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
        femurLandmarks = {}
        meshParams = self._models['right femur'].field_parameters
        for label, ldmkName in FEMUR_LANDMARKS.items():
            evalLdmk = fml.makeLandmarkEvaluator(ldmkName, self._models['right femur'])
            femurLandmarks['R' + label] = evalLdmk(meshParams)

        self._landmarks.update(femurLandmarks)

    def _getLeftFemurLandmarks(self):
        femurLandmarks = {}
        meshParams = self._models['left femur'].field_parameters
        for label, ldmkName in FEMUR_LANDMARKS.items():
            evalLdmk = fml.makeLandmarkEvaluator(ldmkName, self._models['left femur'])
            femurLandmarks['L' + label] = evalLdmk(meshParams)

        self._landmarks.update(femurLandmarks)

    def _getWholePelvisLandmarks(self):
        # pelvisM = pm.PelvisMeasurements(self._models['pelvis'])
        # pelvisM.calcAcetabulumDiameters()
        # self._landmarks.update(pelvisM.measurements['landmarks_unaligned'].value)
        # self._landmarks['PS'] = (self._landmarks['LSP'] + self._landmarks['RSP'])/2.0

        pelvisLandmarks = {}
        meshParams = self._models['pelvis'].field_parameters
        for label, ldmkName in PELVIS_LANDMARKS.items():
            evalLdmk = fml.makeLandmarkEvaluator(ldmkName, self._models['pelvis'])
            pelvisLandmarks[label] = evalLdmk(meshParams)

        self._landmarks.update(pelvisLandmarks)

    def _getPelvisLandmarks(self):
        combPelvisGF = geometric_field.GeometricField(
            'combined pelvis', 3, field_dimensions=2,
            field_basis={'tri10': 'simplex_L3_L3', 'quad44': 'quad_L3_L3'})
        combPelvisGF.ensemble_field_function.name = 'pelvis_combined_cubic'
        combPelvisGF.ensemble_field_function.mesh.name = 'pelvis_combined_cubic'
        combPelvisGF.add_element_with_parameters(
            self._models['right hemi-pelvis'].ensemble_field_function,
            self._models['right hemi-pelvis'].get_field_parameters(),
            tol=0)
        combPelvisGF.add_element_with_parameters(
            self._models['left hemi-pelvis'].ensemble_field_function,
            self._models['left hemi-pelvis'].get_field_parameters(),
            tol=0)
        combPelvisGF.add_element_with_parameters(
            self._models['sacrum'].ensemble_field_function,
            self._models['sacrum'].get_field_parameters(),
            tol=0)

        pelvisM = pm.PelvisMeasurements(combPelvisGF)
        self._landmarks.update(pelvisM.measurements['landmarks_unaligned'].value)
        # self._landmarks['PS'] = (self._landmarks['LSP'] + self._landmarks['RSP'])/2.0

    def setPortData(self, index, dataIn):
        '''
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.
        '''
        self._models = dataIn  # ju#fieldworkmodeldict

    def getPortData(self, index):
        '''
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.
        '''
        return self._landmarks  # ju#landmarks

    def configure(self):
        '''
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        '''

        self._configured = True

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

    def serialize(self):
        '''
        Add code to serialize this step to disk. Returns a json string for
        mapclient to serialise.
        '''
        return ''

    def deserialize(self, string):
        '''
        Add code to deserialize this step from disk. Parses a json string
        given by mapclient
        '''
        pass
