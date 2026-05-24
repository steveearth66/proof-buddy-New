import '../scss/_definitions.scss';
import Form from 'react-bootstrap/Form';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/esm/Button';
import Accordion from 'react-bootstrap/Accordion';
import Modal from 'react-bootstrap/Modal';
import { Eye, EyeSlash } from 'react-bootstrap-icons';
import validateField from '../utils/definitionsFormValidation';
import { useInputState } from '../hooks/useInputState';
import { useFormValidation } from '../hooks/useFormValidation';
import { useFormSubmit } from '../hooks/useFormSubmit';
import { useParenHighlight } from '../hooks/useParenHighlight';
import { useEffect, useState } from 'react';
import erService from '../services/erService';
import { toast } from 'react-toastify';
import { createPortal } from 'react-dom';
import RacketInput from './RacketInput';

export default function Definitions({ toggleDefinitionsWindow, isLocked = false, isStudent = false, validateHiddenDefinitionFn }) {
  const [showCreateDefinition, setShowCreateDefinition] = useState(false);

  return createPortal(
    <div className="overlay">
      <div className="card">
        {showCreateDefinition ? (
          <CreateDefinition
            onUpdate={setShowCreateDefinition}
            isLocked={isLocked}
            isStudent={isStudent}
          />
        ) : (
          <ShowDefinitions
            onUpdate={setShowCreateDefinition}
            toggleDefinitionsWindow={toggleDefinitionsWindow}
            isLocked={isLocked}
            isStudent={isStudent}
          />
        )}
      </div>
    </div>,
      document.body
  );
}

function CreateDefinition({
  onUpdate,
  id,
  label,
  type,
  expression,
  notes,
  edit,
  updateDefinition,
  isLocked = false,
  isStudent = false,
  expressionHiddenInit = false,
  onConvertToGeneric = null
}) {
  const initialValues = {
    label: label || '',
    type: type || '',
    expression: expression || '',
    notes: notes || ''
  };

  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const [errors, setErrors] = useState([]);
  const [successMessage, setSuccessMessage] = useState('');
  const [expressionHidden, setExpressionHidden] = useState(expressionHiddenInit);
  const [showChoiceModal, setShowChoiceModal] = useState(false);
  
  // Parenthesis highlighting for each field
  const { 
    highlightPositions: labelHighlights, 
    inputRef: labelRef, 
    handleKeyUp: labelKeyUp, 
    handleSelect: labelSelect 
  } = useParenHighlight(formValues.label);
  
  const { 
    highlightPositions: typeHighlights, 
    inputRef: typeRef, 
    handleKeyUp: typeKeyUp, 
    handleSelect: typeSelect 
  } = useParenHighlight(formValues.type);
  
  const { 
    highlightPositions: exprHighlights, 
    inputRef: exprRef, 
    handleKeyUp: exprKeyUp, 
    handleSelect: exprSelect 
  } = useParenHighlight(formValues.expression);

  const handleReset = () => {
    formValues.label = '';
    formValues.type = '';
    formValues.expression = '';
    formValues.notes = '';
    setValidated(false);
    setErrors([]);
  };

  const doCreateGeneric = async () => {
    const generics_ss = JSON.parse(sessionStorage.getItem('generics')) || [];
    const generic = {
      id,
      label: formValues.label,
      type: formValues.type,
      expression: '',
      notes: formValues.notes,
      applied: true,
      expression_hidden: false,
    };
    if (generic.type.toLowerCase() === 'int')
      generic.restrictions = { assumption: 'Non-negative' };
    if (generic.type.toLowerCase() === 'list')
      generic.restrictions = { neverNull: true };
    try {
      const createdGeneric = await erService.createGeneric(generic);
      createdGeneric.enabled = true;
      generics_ss.push(createdGeneric);
      sessionStorage.setItem('generics', JSON.stringify(generics_ss));
      setSuccessMessage('Generic created successfully.');
      setErrors([]);
      handleReset();
    } catch (error) {
      if (error.response?.data?.message) {
        setErrors([error.response.data.message]);
      } else {
        setErrors(['An error occurred. Please try again']);
      }
      setValidated(false);
    }
  };

  const doCreateStudentEntry = async () => {
    const definitions_ss = JSON.parse(sessionStorage.getItem('definitions')) || [];
    const definition = {
      id,
      label: formValues.label,
      type: formValues.type,
      expression: '',
      notes: formValues.notes,
      applied: true,
      expression_hidden: true,
    };
    try {
      const createdDefinition = await erService.createDefinition(definition);
      if (createdDefinition) {
        createdDefinition.type = createdDefinition.def_type;
        definitions_ss.push(createdDefinition);
        sessionStorage.setItem('definitions', JSON.stringify(definitions_ss));
        setSuccessMessage('Student-entry definition created successfully.');
        setErrors([]);
        handleReset();
      } else {
        setErrors(['An error occurred. Please try again.']);
        setValidated(false);
      }
    } catch (error) {
      if (error.response?.data?.message) {
        setErrors(Array.isArray(error.response.data.message) ? error.response.data.message : [error.response.data.message]);
      } else {
        setErrors(['An error occurred. Please try again.']);
      }
      setValidated(false);
    }
  };

  const doEditAsStudentEntry = async () => {
    const definition = {
      id,
      label: formValues.label,
      type: formValues.type,
      expression: '',
      notes: formValues.notes,
      applied: true,
      expression_hidden: true,
    };
    try {
      const newDefinition = await toast.promise(
        erService.editDefinition(definition),
        {
          pending: 'Updating definition...',
          success: 'Definition updated successfully.',
          error: 'An error occurred. Please try again.'
        }
      );
      setErrors([]);
      updateDefinition({
        id: newDefinition.id,
        label: newDefinition.label,
        type: newDefinition.def_type,
        expression: newDefinition.expression,
        notes: newDefinition.notes,
        expression_hidden: true
      });
      onUpdate(false);
    } catch (error) {
      if (error.response && error.response.data && error.response.data.message) {
        setErrors(Array.isArray(error.response.data.message) ? error.response.data.message : [error.response.data.message]);
      } else {
        setErrors(['An error occurred. Please try again.']);
      }
      setValidated(false);
    }
  };

  const doEditAsGeneric = async () => {
    try {
      await erService.deleteDefinition(formValues.label);
      const generic = {
        label: formValues.label,
        type: formValues.type,
        expression: '',
        notes: formValues.notes,
        applied: true,
        expression_hidden: false,
      };
      if (generic.type.toLowerCase() === 'int')
        generic.restrictions = { assumption: 'Non-negative' };
      if (generic.type.toLowerCase() === 'list')
        generic.restrictions = { neverNull: true };
      const createdGeneric = await toast.promise(
        erService.createGeneric(generic),
        {
          pending: 'Converting to generic...',
          success: 'Generic created successfully.',
          error: 'An error occurred. Please try again.'
        }
      );
      createdGeneric.enabled = true;
      onConvertToGeneric(formValues.label, createdGeneric);
    } catch (error) {
      if (error.response?.data?.message) {
        setErrors([error.response.data.message]);
      } else {
        setErrors(['An error occurred. Please try again.']);
      }
      setValidated(false);
    }
  };

  const handleCreateDefinition = async () => {
    const definition = {
      id,
      label: formValues.label,
      type: formValues.type,
      expression: formValues.expression,
      notes: formValues.notes,
      applied: true,
      expression_hidden: expressionHidden,
    };

    const definitions = JSON.parse(sessionStorage.getItem('definitions')) || [];
    const generics = JSON.parse(sessionStorage.getItem('generics')) || [];
    let exists = false;

    if (edit) {
      if (!definition.expression && !expressionHidden) {
        setShowChoiceModal(true);
        return;
      }
      try {
        const newDefinition = await toast.promise(
          erService.editDefinition(definition),
          {
            pending: 'Updating definition...',
            success: 'Definition updated successfully.',
            error: 'An error occurred. Please try again.'
          }
        );
        setErrors([]);

        updateDefinition({
          id: newDefinition.id,
          label: newDefinition.label,
          type: newDefinition.def_type,
          expression: newDefinition.expression,
          notes: newDefinition.notes,
          expression_hidden: expressionHidden
        });
      } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
          setErrors(Array.isArray(error.response.data.message) ? error.response.data.message : [error.response.data.message]);
        } else {
          setErrors(['An error occurred. Please try again.']); // generic error message
        }
        setValidated(false);
      }
      return;
    }

    const existingLabels = [...definitions, ...generics].map(obj => obj.label.split(" ")[0]);
    if (existingLabels.includes(definition.label.split(" ")[0])) {
      setErrors(['Definition or generic with this label already exists.']);
      exists = true;
    }

    if (!exists) {
      if (!definition.expression) {
        if (!expressionHidden) {
          setShowChoiceModal(true);
          return;
        }
        await doCreateStudentEntry();
        return;
      }
      try {
        const createdDefinition = await erService.createDefinition(definition);
        setErrors([]);

        if (createdDefinition) {
          createdDefinition.type = createdDefinition.def_type;
          definitions.push(createdDefinition);
          sessionStorage.setItem('definitions', JSON.stringify(definitions));
          setSuccessMessage('Definition created successfully.');
          handleReset();
        } else {
          setErrors(['An error occurred. Please try again.']);
          setValidated(false);
        }
      } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
          setErrors(Array.isArray(error.response.data.message) ? error.response.data.message : [error.response.data.message]);
        } else {
          setErrors(['An error occurred. Please try again.']); // generic error message
        }
        setValidated(false);
      }
    }
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleCreateDefinition
  );

  return (
    <div className="create-definition">
      {edit ? (
        <p className="title"> Edit definition </p>
      ) : (
        <p className="title"> Create a new definition </p>
      )}

      {errors.length > 0 && (
        <Alert variant="danger" className="scroll-error">
          {errors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </Alert>
      )}

      {successMessage && <Alert variant="success">{successMessage}</Alert>}

      <Form
        className="form"
        noValidate
        validated={validated}
        onSubmit={handleSubmit}
      >
        <Row>
          <Col>
            <div className="label-field-container">
              <label htmlFor="definitionLabel" className="form-label">Label</label>
              <RacketInput
                type="text"
                id="definitionLabel"
                name="label"
                placeholder="Enter Label"
                value={formValues.label}
                onBlur={() => handleBlur('label')}
                onChange={handleChange}
                onKeyUp={labelKeyUp}
                onClick={labelSelect}
                ref={labelRef}
                highlightPositions={labelHighlights}
                isInvalid={!!validationMessages.label}
                required
              />
              <Form.Control.Feedback type="invalid">
                {validationMessages.label}
              </Form.Control.Feedback>
            </div>
          </Col>
          <Col>
            <div className="type-field-container">
              <label htmlFor="definitionType" className="form-label">Type</label>
              <RacketInput
                type="text"
                id="definitionType"
                name="type"
                placeholder="Enter Type"
                value={formValues.type}
                onBlur={() => handleBlur('type')}
                onChange={handleChange}
                onKeyUp={typeKeyUp}
                onClick={typeSelect}
                ref={typeRef}
                highlightPositions={typeHighlights}
                isInvalid={!!validationMessages.type}
                required
              />
              <Form.Control.Feedback type="invalid">
                {validationMessages.type}
              </Form.Control.Feedback>
            </div>
          </Col>
        </Row>
        <Row>
          <Col>
            <div className="expression-field-container">
              <label htmlFor="definitionExpression" className="form-label">Expression (leave blank to declare a generic)</label>
              <RacketInput
                type="text"
                id="definitionExpression"
                name="expression"
                placeholder="Enter Expression"
                value={formValues.expression}
                onBlur={() => handleBlur('expression')}
                onChange={handleChange}
                onKeyUp={exprKeyUp}
                onClick={exprSelect}
                ref={exprRef}
                highlightPositions={exprHighlights}
                style={{ height: '120px' }}
              />
              <Form.Control.Feedback type="invalid">
                {validationMessages.expression}
              </Form.Control.Feedback>
            </div>
          </Col>
        </Row>
        <Row>
          <Col>
            <Form.Control
              type="text"
              id="definitionNotes"
              name="notes"
              placeholder="Enter Notes"
              value={formValues.notes}
              onBlur={() => handleBlur('notes')}
              onChange={handleChange}
              as="textarea"
              rows={4}
            />
          </Col>
        </Row>
        {!isStudent && (
          <div className="d-flex justify-content-center align-items-center mt-2" style={{ gap: '8px' }}>
            <Button
              variant="link"
              type="button"
              onClick={() => setExpressionHidden(prev => !prev)}
              title="Toggle visibility"
              style={{ color: expressionHidden ? 'red' : 'green', fontSize: '1.5rem', padding: '0' }}
            >
              {expressionHidden ? <EyeSlash /> : <Eye />}
            </Button>
            <span style={{ color: expressionHidden ? 'red' : 'green', fontSize: '0.9rem' }}>
              {!expressionHidden
                ? 'function definition visible to users'
                : formValues.expression
                  ? 'function definition hidden from users'
                  : 'user supplies function implementation'}
            </span>
          </div>
        )}
        <div className="def-button-row">
          <Button variant="outline-danger" onClick={() => onUpdate(false)}>
            Go Back
          </Button>
          <Button variant="outline-primary" type="submit" disabled={isLocked}>
            {edit ? 'Update' : 'Create'} Definition
          </Button>
        </div>
      </Form>
      <Modal show={showChoiceModal} onHide={() => setShowChoiceModal(false)} className="definition-choice-modal" backdropClassName="definition-choice-modal-backdrop">
        <Modal.Header closeButton>
          <Modal.Title>No expression entered</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Do you wish to create a generic {formValues.type} free variable, or have the student enter their own implementation?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-success" onClick={() => { setShowChoiceModal(false); edit ? doEditAsGeneric() : doCreateGeneric(); }}>
            Create Generic
          </Button>
          <Button variant="outline-primary" onClick={() => { setShowChoiceModal(false); edit ? doEditAsStudentEntry() : doCreateStudentEntry(); }}>
            Student Entry
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

function ShowDefinitions({ onUpdate, toggleDefinitionsWindow, isLocked = false, isStudent = false }) {
  const [definitions, setDefinitions] = useState(
    JSON.parse(sessionStorage.getItem('definitions')) || []
  );
  const [generics, setGenerics] = useState(() => {
    const stored = JSON.parse(sessionStorage.getItem('generics')) || [];
    return stored;
  });
  const [definitionToEdit, setDefinitionToEdit] = useState({});
  const [edit, setEdit] = useState(false);
  const [genericToEdit, setGenericToEdit] = useState({});
  const [editGeneric, setEditGeneric] = useState(false);
  
  const [tempDefinitions] = useState(JSON.parse(sessionStorage.getItem('temp_definitions')) || []);
  const [tempGenerics] = useState(JSON.parse(sessionStorage.getItem('temp_generics')) || []);

  // Re-sync with sessionStorage whenever component becomes visible
  // (in case generics were updated while panel was closed)
  useEffect(() => {
    const syncGenerics = () => {
      const stored = JSON.parse(sessionStorage.getItem('generics')) || [];
      setGenerics(stored);
    };
    
    // Sync immediately when component mounts/opens
    syncGenerics();
    
    // Also listen for visibility changes
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        syncGenerics();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    const handleGenericsUpdated = (event) => {
      const { newGeneric, allGenerics } = event.detail;
      
      if (allGenerics) {
        setGenerics(allGenerics);
      } else if (newGeneric) {
        setGenerics(prev => {
          const existingIndex = prev.findIndex(g => g.label === newGeneric.label);
          
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = newGeneric;
            return updated;
          } else {
            return [...prev, newGeneric];
          }
        });
      }
    };

    window.addEventListener('genericsUpdated', handleGenericsUpdated);
    
    return () => {
      window.removeEventListener('genericsUpdated', handleGenericsUpdated);
    };
  }, []);

  const deleteDefinition = async (label) => {
    const confirm = window.confirm(
      'Are you sure you want to delete this definition?'
    );
    if (!confirm) return;
    const deleted = await toast.promise(erService.deleteDefinition(label), {
      pending: 'Deleting definition...',
      success: 'Definition deleted successfully.',
      error: 'An error occurred. Please try again.'
    });

    if (!deleted) return;

    const definitions = JSON.parse(sessionStorage.getItem('definitions')) || [];
    const updatedDefinitions = definitions.filter((def) => def.label !== label);
    sessionStorage.setItem('definitions', JSON.stringify(updatedDefinitions));
    setDefinitions(updatedDefinitions);
  };

  const deleteGeneric = async (generic) => {
    try {
      await toast.promise(erService.deleteGeneric(generic.id), {
        pending: 'Deleting generic...',
        success: 'Generic deleted successfully.',
        error: 'An error occurred. Please try again.'
      });
      setGenerics(prev => {
        const updatedGenerics = prev.filter(gen => gen.id !== generic.id);
        sessionStorage.setItem('generics', JSON.stringify(updatedGenerics));
        return updatedGenerics;
      });
    } catch (error) {
      console.error(error)
    }
  };

  const updateDefinition = async ({ id, label, type, expression, notes, expression_hidden }) => {
    const updatedDefinitions = definitions.map((def) => {
      if (def.id === id) {
        return { id, label, type, expression, notes, expression_hidden };
      } else {
        return def;
      }
    });
    sessionStorage.setItem('definitions', JSON.stringify(updatedDefinitions));
    setDefinitions(updatedDefinitions);
  };

  const updateGenericEdit = (generic) => {
    setGenericToEdit(generic);
    setEditGeneric(true);
  };

  const onGenericUpdated = (oldId, createdGeneric) => {
    setGenerics(prev => {
      const updated = [...prev.filter(g => g.id !== oldId), createdGeneric];
      sessionStorage.setItem('generics', JSON.stringify(updated));
      return updated;
    });
    setEditGeneric(false);
  };

  const handleConvertFromGeneric = (oldId, createdDefinition) => {
    setGenerics(prev => {
      const updated = prev.filter(g => g.id !== oldId);
      sessionStorage.setItem('generics', JSON.stringify(updated));
      return updated;
    });
    setDefinitions(prev => {
      const updated = [...prev, createdDefinition];
      sessionStorage.setItem('definitions', JSON.stringify(updated));
      return updated;
    });
    setEditGeneric(false);
  };

  const handleConvertToGeneric = (label, createdGeneric) => {
    setDefinitions(prev => {
      const updated = prev.filter(d => d.label !== label);
      sessionStorage.setItem('definitions', JSON.stringify(updated));
      return updated;
    });
    setGenerics(prev => {
      const updated = [...prev, createdGeneric];
      sessionStorage.setItem('generics', JSON.stringify(updated));
      return updated;
    });
    setEdit(false);
  };

  const updateEdit = (definition) => {
    setDefinitionToEdit(definition);
    setEdit(true);
  };

  //const applyDefinition = async (id, applied) => {
  const applyDefinition = async (label, applied) => {
    if (applied) {
      try {
        //await toast.promise(erService.removeDefinition(id), {
        await toast.promise(erService.removeDefinition(label), {
          pending: 'Disabling definition...',
          success: 'Definition disabled successfully.',
          error: 'An error occurred. Please try again.'
        });
        setDefinitions((prev) => {
          const updated = prev.map((def) => {
            //if (def.id === id) {
            if (def.label === label) {
              def.applied = false;
            }
            return def;
          });
          sessionStorage.setItem('definitions', JSON.stringify(updated)); // use updated array, not stale closure
          return updated;
        });
      } catch (error) {
        console.error(error);
      }
    } else {
      try {
        //await toast.promise(erService.useDefinition(id), {
        await toast.promise(erService.useDefinition(label), {
          pending: 'Enabling definition...',
          success: 'Definition enabled successfully.',
          error: 'An error occurred. Please try again.'
        });
        setDefinitions((prev) => {
          const updated = prev.map((def) => {
            //if (def.id === id) {
            if (def.label === label) {
              def.applied = true;
            }
            return def;
          });
          sessionStorage.setItem('definitions', JSON.stringify(updated)); // use updated array, not stale closure
          return updated;
        });
      } catch (error) {
        console.error(error);
      }
    }
  };

  const enableGeneric = async (generic) => {
    if (generic.enabled) {
      try {
        await toast.promise(erService.removeGeneric(generic.id), {
          pending: 'Disabling generic...',
          success: 'Generic successfully disabled.',
          error: 'An error occurred. Please try again.'
        });
        setGenerics(prev => {
          const updated = prev.map(gen =>
            gen.id === generic.id ? { ...gen, enabled: false } : gen
          );
          sessionStorage.setItem('generics', JSON.stringify(updated));
          return updated;
        });
      } catch (error) {
        console.error(error);
      }
    } else {
      try {
        await toast.promise(erService.useGeneric(generic.id), {
          pending: 'Enabling generic...',
          success: 'Generic successfully enabled.',
          error: 'An error occurred. Please try again.'
        });
        setGenerics(prev => {
          const updated = prev.map(gen =>
            gen.id === generic.id ? { ...gen, enabled: true } : gen
          );
          sessionStorage.setItem('generics', JSON.stringify(updated));
          return updated;
        });
      } catch (error) {
        if (error.response?.data?.message)
          console.error(error.response.data.message);
        else
          console.error(error);
      }
    }
  };

  useEffect(() => {
    erService.getUserDefinitions().then((userDefinitions) => {
      let newDefinitions = [];
      userDefinitions.forEach((def) => {
        const foundDef = definitions.find(d => d.label === def.label);
        if (foundDef) {
          foundDef.applied = foundDef.applied ? true : false;
          newDefinitions.push(foundDef);
        } else {
          newDefinitions.push(def);
        }
      });
      setDefinitions(newDefinitions);
      sessionStorage.setItem('definitions', JSON.stringify(newDefinitions));
    }).catch((error) => {
      console.error('Failed to load user definitions:', error);
      toast.error('Failed to load definitions. Please try refreshing the page.');
    });
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    erService.getUserGenerics().then(userGenerics => {
      const storedGenerics = JSON.parse(sessionStorage.getItem('generics')) || [];
      
      // Merge: prefer backend data but preserve 'enabled' state from sessionStorage
      const merged = userGenerics;
      
      // Add any sessionStorage generics that don't exist in backend yet
      storedGenerics.forEach(stored => {
        const existsInBackend = merged.find(ug => ug.label === stored.label || ug.name === stored.name);
        if (!existsInBackend) {
          merged.push(stored);
        }
      });
      setGenerics(merged);
      sessionStorage.setItem('generics', JSON.stringify(merged));
    }).catch(error => {
      console.error('Error fetching user generics:', error);
      // On error, just use what's in sessionStorage
      const storedGenerics = JSON.parse(sessionStorage.getItem('generics')) || [];
      setGenerics(storedGenerics);
    });
  }, []);

  useEffect(() => {
  }, [generics]);

  if (editGeneric) {
    return (
      <EditGeneric
        generic={genericToEdit}
        onBack={() => setEditGeneric(false)}
        onGenericUpdated={onGenericUpdated}
        onConvertToDefinition={handleConvertFromGeneric}
        isLocked={isLocked}
      />
    );
  }

  if (edit) {
    return (
      <CreateDefinition
        onUpdate={() => setEdit(false)}
        id={definitionToEdit.id}
        label={definitionToEdit.label}
        type={definitionToEdit.type}
        expression={definitionToEdit.expression}
        notes={definitionToEdit.notes}
        edit={edit}
        updateDefinition={updateDefinition}
        isLocked={isLocked}
        isStudent={isStudent}
        expressionHiddenInit={definitionToEdit.expression_hidden || false}
        onConvertToGeneric={handleConvertToGeneric}
      />
    );
  } else {
    return (
      <div className="definitions-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '85vh' }}>
        
        <div style={{ flexGrow: 1, overflowY: 'auto', paddingRight: '5px' }}>
          <Accordion defaultActiveKey={['default-defs', 'user-defs', 'user-gens']} alwaysOpen>
            
            <Accordion.Item eventKey='default-defs'>
              <Accordion.Header className="def-section"><p className="title mb-0">Default definitions</p></Accordion.Header>
              <Accordion.Body>
                <div className="definitions" style={{ maxHeight: '35vh', overflowY: 'auto', paddingRight: '10px' }}>
                  {definitions.filter(d => d.is_default).map((def, index) => (
                    <Definition
                      key={index}
                      definition={def}
                      eventKey={index}
                      deleteDefinition={deleteDefinition}
                      updateEdit={updateEdit}
                      applyDefinition={applyDefinition}
                      isLocked={isLocked}
                    />
                  ))}
                </div>
              </Accordion.Body>
            </Accordion.Item>

            <Accordion.Item eventKey='user-defs'>
              <Accordion.Header><p className="title mb-0">User definitions</p></Accordion.Header>
              <Accordion.Body>
                <div className="definitions" style={{ maxHeight: '35vh', overflowY: 'auto', paddingRight: '10px' }}>
                  {definitions.filter(d => !d.is_default).map((def, index) => (
                    <Definition
                      key={index}
                      definition={def}
                      eventKey={index}
                      deleteDefinition={deleteDefinition}
                      updateEdit={updateEdit}
                      applyDefinition={applyDefinition}
                      isLocked={isLocked}
                    />
                  ))}
                </div>
              </Accordion.Body>
            </Accordion.Item>

          {(tempDefinitions.length > 0) && (
            <Accordion.Item eventKey='proof-defs'>
              <Accordion.Header><p className="title mb-0">Proof definitions</p></Accordion.Header>
              <Accordion.Body>
                <div className="definitions" style={{ maxHeight: '35vh', overflowY: 'auto', paddingRight: '10px' }}>
                  {tempDefinitions.map((def, i) => (
                    <Definition 
                      key={`temp-def-${def.id || i}`}
                      eventKey={`temp-def-${def.id || i}`}
                      definition={{ ...def, applied: true }} 
                      isLocked={true}
                    />
                  ))}
                </div>
              </Accordion.Body>
            </Accordion.Item>
          )}

          <Accordion.Item eventKey='user-gens'>
            <Accordion.Header><p className="title mb-0">User Generics</p></Accordion.Header>
            <Accordion.Body>
              <div className="generics" style={{ maxHeight: '35vh', overflowY: 'auto', paddingRight: '10px' }}>
              {generics.map((gen, index) => (
                <Generic
                  key={index}
                  generic={gen}
                  eventKey={index}
                  enableGeneric={enableGeneric}
                  deleteGeneric={deleteGeneric}
                  updateGenericEdit={updateGenericEdit}
                  isLocked={isLocked}
                />
              ))}
            </div>
            </Accordion.Body>
          </Accordion.Item>

          {tempGenerics.length > 0 && (
            <Accordion.Item eventKey='proof-gens'>
              <Accordion.Header><p className="title mb-0">Proof Generics</p></Accordion.Header>
              <Accordion.Body>
                <div className="generics" style={{ maxHeight: '35vh', overflowY: 'auto', paddingRight: '10px' }}>
                  {tempGenerics.map((gen, i) => (
                    <Generic 
                      key={`temp-gen-${gen.id || i}`} 
                      eventKey={`temp-gen-${gen.id || i}`}
                      generic={{ ...gen, enabled: true }} 
                      isLocked={true} 
                    />
                  ))}
                </div>
              </Accordion.Body>
            </Accordion.Item>
          )}
          </Accordion>
        </div>

        <div className="def-button-row" style={{
            marginTop: 'auto', 
            paddingTop: '15px',
            borderTop: '1px solid #dee2e6',
            display: 'flex',
            justifyContent: 'space-between',
            backgroundColor: 'white',
            zIndex: 10
        }}>
          <Button variant="danger" onClick={toggleDefinitionsWindow}>
            Close Definitions Window
          </Button>
          <Button onClick={() => onUpdate(true)} disabled={isLocked}>
            Create New Definition
          </Button>
        </div>
      </div>
    );
  }
}

function Definition({
  definition,
  eventKey,
  deleteDefinition,
  updateEdit,
  applyDefinition,
  isLocked = false
}) {
  const isDefaultUDF = definition.is_default === true || definition.deletable === false;
  
  return (
    <Accordion>
      <Accordion.Item eventKey={eventKey}>
        <Accordion.Header>
          <p className="definition-label">{definition.label}</p>
        </Accordion.Header>
        <Accordion.Body>
          <p>Type: {definition.type}</p>
          <p>
            Expression:{' '}
            {definition.expression_hidden && !definition.expression
              ? <span style={{ color: 'red' }}>user supplied</span>
              : definition.expression}
          </p>
          <p>Visibility: {definition.expression_hidden ? 'Hidden' : 'Visible'}</p>
          {definition.notes && <p>Notes: {definition.notes}</p>}
          <div className="def-buttons">
            <Button
              variant={`${definition.applied ? "outline-danger" : "outline-success"}`}
                //onClick={() => applyDefinition(definition.id, definition.applied)}
              onClick={() => applyDefinition(definition.label, definition.applied)}
              disabled={isLocked}
            >
              {definition.applied ? "Disable" : "Enable"} Definition
            </Button>
            <Button
              variant="outline-primary"
              onClick={() => updateEdit(definition)}
              disabled={isDefaultUDF || isLocked}
            >
              Edit
            </Button>
            <Button
              variant="outline-danger"
              //onClick={() => deleteDefinition(definition.id)}
              onClick={() => deleteDefinition(definition.label)}
              disabled={isDefaultUDF || isLocked}
            >
              Delete
            </Button>
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}

function EditGeneric({ generic, onBack, onGenericUpdated, onConvertToDefinition, isLocked = false }) {
  const [label, setLabel] = useState(generic.label);
  const [type, setType] = useState(generic.type);
  const [expression, setExpression] = useState('');
  const [notes, setNotes] = useState(generic.notes || '');
  const [errors, setErrors] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!label.trim() || !type.trim()) {
      setErrors(['Label and type are required.']);
      return;
    }
    try {
      if (expression.trim()) {
        // Convert to definition — backend atomically removes the generic and creates the definition
        const newDefinition = {
          label: label.trim(),
          type: type.trim(),
          expression: expression.trim(),
          notes: notes.trim(),
          applied: true,
          expression_hidden: false,
        };
        const created = await toast.promise(
          erService.createDefinition(newDefinition),
          {
            pending: 'Converting to definition...',
            success: 'Definition created successfully.',
            error: 'An error occurred. Please try again.'
          }
        );
        if (created) {
          created.type = created.def_type;
          onConvertToDefinition(generic.id, created);
        }
      } else {
        await erService.deleteGeneric(generic.id);
        const newGeneric = {
          label: label.trim(),
          type: type.trim(),
          expression: '',
          notes: notes.trim(),
          applied: true,
          expression_hidden: false,
        };
        if (newGeneric.type.toLowerCase() === 'int')
          newGeneric.restrictions = { assumption: 'Non-negative' };
        if (newGeneric.type.toLowerCase() === 'list')
          newGeneric.restrictions = { neverNull: true };
        const created = await toast.promise(
          erService.createGeneric(newGeneric),
          {
            pending: 'Updating generic...',
            success: 'Generic updated successfully.',
            error: 'An error occurred. Please try again.'
          }
        );
        created.enabled = true;
        onGenericUpdated(generic.id, created);
      }
    } catch (error) {
      if (error.response?.data?.message) {
        setErrors([error.response.data.message]);
      } else {
        setErrors(['An error occurred. Please try again.']);
      }
    }
  };

  return (
    <div>
      <h4>Edit Generic</h4>
      {errors.length > 0 && (
        <Alert variant="danger" className="scroll-error">
          {errors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </Alert>
      )}
      <Form className="form" onSubmit={handleSubmit}>
        <Row>
          <Col>
            <div className="label-field-container">
              <label className="form-label">Label</label>
              <RacketInput
                type="text"
                name="label"
                placeholder="Enter Label"
                value={label}
                onChange={e => setLabel(e.target.value)}
                disabled={isLocked}
                required
              />
            </div>
          </Col>
          <Col>
            <div className="type-field-container">
              <label className="form-label">Type</label>
              <RacketInput
                type="text"
                name="type"
                placeholder="Enter Type"
                value={type}
                onChange={e => setType(e.target.value)}
                disabled={isLocked}
                required
              />
            </div>
          </Col>
        </Row>
        <Row>
          <Col>
            <div className="expression-field-container">
              <label className="form-label">Expression (leave blank to keep as generic)</label>
              <RacketInput
                type="text"
                name="expression"
                placeholder="Enter Expression"
                value={expression}
                onChange={e => setExpression(e.target.value)}
                disabled={isLocked}
              />
            </div>
          </Col>
        </Row>
        <Row>
          <Col>
            <div>
              <label className="form-label">Notes</label>
              <Form.Control
                as="textarea"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                disabled={isLocked}
              />
            </div>
          </Col>
        </Row>
        <div className="def-button-row">
          <Button variant="outline-danger" type="button" onClick={onBack}>
            Go Back
          </Button>
          <Button variant="outline-primary" type="submit" disabled={isLocked}>
            Update Generic
          </Button>
        </div>
      </Form>
    </div>
  );
}

function Generic({
  generic,
  eventKey,
  enableGeneric,
  deleteGeneric,
  updateGenericEdit,
  isLocked = false
}) {

  const restrictionsToString = restrictions => {
    let restrictionStr = '';
    if (restrictions.assumption && restrictions.assumption !== 'None') {
      restrictionStr += restrictions.assumption.toLowerCase();
    }
    if (restrictions.neverNull) {
      restrictionStr += 'cannot be null';
    }
    return restrictionStr;
  }

  return (
    <Accordion>
      <Accordion.Item eventKey={eventKey}>
        <Accordion.Header>
          <p className="generic-label">{generic.label}</p>
        </Accordion.Header>
        <Accordion.Body>
          <p>Type: {generic.type}</p>

          {(generic.type === 'int' || generic.type === 'list') && 
          <p>Restrictions: {restrictionsToString(generic.restrictions)}</p>}
          {generic.type === 'any' && <p>Restrictions: nonnegative, cannot be null</p>}

          {generic.notes && <p>Notes: {generic.notes}</p>}
          <div className="def-buttons">
            <Button
              variant={`${generic.enabled ? "outline-danger" : "outline-success"}`}
              onClick={() => enableGeneric(generic)}
              disabled={isLocked}
            >
              {generic.enabled ? "Disable" : "Enable"} Generic
            </Button>
            {updateGenericEdit && (
              <Button
                variant="outline-primary"
                onClick={() => updateGenericEdit(generic)}
                disabled={isLocked}
              >
                Edit
              </Button>
            )}
            <Button
              variant="outline-danger"
              onClick={() => deleteGeneric(generic)}
              disabled={isLocked}
            >
              Delete
            </Button>
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  )
}