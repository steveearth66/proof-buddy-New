import '../scss/_definitions.scss';
import Form from 'react-bootstrap/Form';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/esm/Button';
import Accordion from 'react-bootstrap/Accordion';
import validateField from '../utils/definitionsFormValidation';
import { useInputState } from '../hooks/useInputState';
import { useFormValidation } from '../hooks/useFormValidation';
import { useFormSubmit } from '../hooks/useFormSubmit';
import { useEffect, useState } from 'react';
import erService from '../services/erService';
import { toast } from 'react-toastify';
import { createPortal } from 'react-dom';

export default function Definitions({ toggleDefinitionsWindow }) {
  const [showCreateDefinition, setShowCreateDefinition] = useState(false);

  return createPortal(
    <div className="overlay">
      <div className="card">
        {showCreateDefinition ? (
          <CreateDefinition onUpdate={setShowCreateDefinition} />
        ) : (
          <ShowDefinitions
            onUpdate={setShowCreateDefinition}
            toggleDefinitionsWindow={toggleDefinitionsWindow}
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
  updateDefinition
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

  const handleReset = () => {
    formValues.label = '';
    formValues.type = '';
    formValues.expression = '';
    formValues.notes = '';
    setValidated(false);
    setErrors([]);
  };

  const handleCreateDefinition = async () => {
    const definition = {
      id,
      label: formValues.label,
      type: formValues.type,
      expression: formValues.expression,
      notes: formValues.notes,
      applied: true
    };

    const definitions = JSON.parse(sessionStorage.getItem('definitions')) || [];
    const generics = JSON.parse(sessionStorage.getItem('generics')) || [];
    let exists = false;

    if (edit) {
      if (!definition.expression) {
        setErrors(['Cannot edit a definition to a generic.']);
        setValidated(false);
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
          notes: newDefinition.notes
        });
      } catch (error) {
        if (error.response && error.response.data && error.response.data.message) {
          setErrors(error.response.data.message);
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
      // Create generic if expression is left blank
      if (!definition.expression) {
        try {
          const generic = definition;
          // Add default restrictions:
          if (generic.type.toLowerCase() === 'int')
            generic.restrictions = { assumption: 'Non-negative' };
          if (generic.type.toLowerCase() === 'list')
            generic.restrictions = { neverNull: true };

          const createdGeneric = await erService.createGeneric(generic);
          generics.push(createdGeneric);
          sessionStorage.setItem('generics', JSON.stringify(generics));
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
      } else {
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
            setErrors(error.response.data.message);
          } else {
            setErrors(['An error occurred. Please try again.']); // generic error message
          }
          setValidated(false);
        }
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
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionLabel"
                name="label"
                placeholder="Enter Label"
                value={formValues.label}
                onBlur={() => handleBlur('label')}
                onChange={handleChange}
                isInvalid={!!validationMessages.label}
                required
              />
              <label htmlFor="definitionLabel">Label</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.label}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
          <Col>
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionType"
                name="type"
                placeholder="Enter Type"
                value={formValues.type}
                onBlur={() => handleBlur('type')}
                onChange={handleChange}
                isInvalid={!!validationMessages.type}
                required
              />
              <label htmlFor="definitionType">Type</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.type}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
        </Row>
        <Row>
          <Col>
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionExpression"
                name="expression"
                placeholder="Enter Expression"
                value={formValues.expression}
                onBlur={() => handleBlur('expression')}
                onChange={handleChange}
              />
              <label htmlFor="definitionExpression">Expression (leave blank to declare a generic)</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.expression}
              </Form.Control.Feedback>
            </Form.Floating>
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
        <div className="def-button-row">
          <Button variant="outline-danger" onClick={() => onUpdate(false)}>
            Go Back
          </Button>
          <Button variant="outline-primary" type="submit">
            {edit ? 'Update' : 'Create'} Definition
          </Button>
        </div>
      </Form>
    </div>
  );
}

function ShowDefinitions({ onUpdate, toggleDefinitionsWindow }) {
  const [definitions, setDefinitions] = useState(
    JSON.parse(sessionStorage.getItem('definitions')) || []
  );
  const [generics, setGenerics] = useState(
    JSON.parse(sessionStorage.getItem('generics')) || []
  );
  const [definitionToEdit, setDefinitionToEdit] = useState({});
  const [edit, setEdit] = useState(false);

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
      const generics = JSON.parse(sessionStorage.getItem('generics'));
      const updatedGenerics = generics.filter(gen => gen.id != generic.id);
      setGenerics(updatedGenerics);
    } catch (error) {
      console.error(error)
    }
  };

  const updateDefinition = async ({ id, label, type, expression, notes }) => {
    const updatedDefinitions = definitions.map((def) => {
      if (def.id === id) {
        return { id, label, type, expression, notes };
      } else {
        return def;
      }
    });
    sessionStorage.setItem('definitions', JSON.stringify(updatedDefinitions));
    setDefinitions(updatedDefinitions);
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
          return prev.map((def) => {
            //if (def.id === id) {
            if (def.label === label) {
              def.applied = false;
            }
            return def;
          });
        });
        sessionStorage.setItem('definitions', JSON.stringify(definitions));
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
          return prev.map((def) => {
            //if (def.id === id) {
            if (def.label === label) {
              def.applied = true;
            }
            return def;
          });
        })
        sessionStorage.setItem('definitions', JSON.stringify(definitions));
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
          const updated = prev.map(gen => {
            if (gen.id === generic.id) {
              gen.enabled = false;
            }
            return gen;
          });
          sessionStorage.setItem('generics', JSON.stringify(updated));
          return updated;
        });
      } catch (error) {
        console.error(error)
      }
    } else {
      try {
        await toast.promise(erService.useGeneric(generic.id), {
          pending: 'Enabling generic...',
          success: 'Generic successfully enabled.',
          error: 'An error occurred. Please try again.'
        });
        setGenerics(prev => {
          const updated = prev.map(gen => {
            if (gen.id === generic.id) {
              gen.enabled = true;
            }
            return gen;
          });
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
            // Merge with any generics already in sessionStorage (from induction)
            const storedGenerics = JSON.parse(sessionStorage.getItem('generics')) || [];
      
      // Merge: prefer backend data but keep any that only exist in storage
      const merged = [...userGenerics];
      
      storedGenerics.forEach(stored => {
        const existsInBackend = userGenerics.find(ug => ug.label === stored.label);
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
      />
    );
  } else {
    return (
      <div className="definitions-container">
        <p className="title">User definitions</p>
        <div className="definitions">
          {definitions.map((def, index) => (
            <Definition
              key={index}
              definition={def}
              eventKey={index}
              deleteDefinition={deleteDefinition}
              updateEdit={updateEdit}
              applyDefinition={applyDefinition}
            />
          ))}
        </div>
        <p className="title">Generics</p>
        <div className="generics">
          {generics.map((gen, index) => (
            <Generic
              key={index}
              generic={gen}
              eventKey={index}
              enableGeneric={enableGeneric}
              deleteGeneric={deleteGeneric}
            />
          ))}
        </div>
        <div className="def-button-row">
          <Button variant="danger" onClick={toggleDefinitionsWindow}>
            Close Definitions Window
          </Button>
          <Button onClick={() => onUpdate(true)}>Create New Definition</Button>
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
  applyDefinition
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
          <p>Expression: {definition.expression}</p>
          {definition.notes && <p>Notes: {definition.notes}</p>}
          <div className="def-buttons">
            <Button
              variant={`${definition.applied ? "outline-danger" : "outline-success"}`}
                //onClick={() => applyDefinition(definition.id, definition.applied)}
              onClick={() => applyDefinition(definition.label, definition.applied)}
            >
              {definition.applied ? "Disable" : "Enable"} Definition
            </Button>
            <Button
              variant="outline-primary"
              onClick={() => updateEdit(definition)}
              disabled={isDefaultUDF}
            >
              Edit
            </Button>
            <Button
              variant="outline-danger"
              //onClick={() => deleteDefinition(definition.id)}
              onClick={() => deleteDefinition(definition.label)}
            >
              Delete
            </Button>
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}

function Generic({
  generic,
  eventKey,
  enableGeneric,
  deleteGeneric
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
            >
              {generic.enabled ? "Disable" : "Enable"} Generic
            </Button>
            <Button
              variant="outline-danger"
              onClick={() => deleteGeneric(generic)}
            >
              Delete
            </Button>
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  )
}