import React, { useEffect, useState } from 'react'
import MainLayout from '../layouts/MainLayout';
import Container from 'react-bootstrap/Container';
import { useAuth } from '../context/AuthContext';
import termService from '../services/termServices';
import Button from 'react-bootstrap/esm/Button';
import '../scss/_terms.scss';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import { toast } from 'react-toastify';

function Terms() {
  const { user } = useAuth();
  const [terms, setTerms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const terms = await termService.getTerms();
        setTerms(terms);
      } catch (error) {
        console.error('Error fetching terms:', error);
      }
    };
    fetchData();
  }, []);
  return (
    <MainLayout>
      {showCreate && <CreateTerm setTerms={setTerms} toggleShowCreate={setShowCreate} />}
      <Container>
        <h1>Terms</h1>
        <SearchBar toggleShowCreate={setShowCreate} isStudent={user?.is_student} />
        <div className='layout'>
          {terms.map((term) => (
            <TermCard key={term.id} term={term} isStudent={user?.is_student} />
          ))}
        </div>
      </Container>
    </MainLayout>
  )
}

function TermCard({ term, isStudent }) {
  return (
    <div className='term-card'>
      <h2>{term.name}</h2>
      {isStudent ? (
        <>
          <p><b>Instructor: </b>{term.instructor.first_name} {term.instructor.last_name}</p>
          <p><b>Instructor Email: </b>{term.instructor.email}</p>
        </>
      ) : <p><b>Student Count: </b>{term.students.length}</p>}
      <Button variant='outline-primary'>View</Button>
    </div>
  )
}

function SearchBar({ isStudent, toggleShowCreate }) {
  return (
    <div className="search-bar">
      <InputGroup>
        <Form.Control
          placeholder="Search for a term"
          aria-label="Search for a term"
          aria-describedby="basic-addon2"
        />
        <Button
          variant="outline-secondary"
          id="button-addon2"
        >
          Search
        </Button>
      </InputGroup>
      {!isStudent && <Button variant='outline-secondary' className='term-button' onClick={() => toggleShowCreate((prev) => !prev)}>Create Term</Button>}
    </div>
  )
}

function CreateTerm({ setTerms, toggleShowCreate }) {
  const [students, setStudents] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const term = {
      name: e.target.name.value,
      students
    };
    try {
      const newTerm = await termService.createTerm(term);
      setTerms((prev) => [...prev, newTerm]);
      toast.success('Term created');
      e.target.name.value = '';
      setStudents([]);
    } catch (error) {
      console.error('Error creating term:', error);
    }
  };

  return (
    <div className='term-overlay'>
      <div className='term-card'>
        <h2>Create Term</h2>
        <Form onSubmit={handleSubmit}>
          <Form.Group controlId='name'>
            <Form.Label>Name</Form.Label>
            <Form.Control type='text' placeholder='Enter term name' />
          </Form.Group>
          <AddStudent students={students} setStudents={setStudents} />
          <div className='button-group'>
            <Button variant='danger' onClick={() => toggleShowCreate((prev) => !prev)}>Close</Button>
            <Button variant='primary' type='submit'>Create</Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

function AddStudent({ students, setStudents }) {
  const [student, setStudent] = useState('');

  const addStudent = async () => {
    const studentAdded = await termService.checkUser(student);
    if (studentAdded) {
      setStudents((prev) => [...prev, student]);
      setStudent('');
      toast.success('Student added');
    } else {
      toast.error('Student not found');
    }
  };

  const removeStudent = (student) => {
    setStudents((prev) => prev.filter((s) => s !== student));
  };

  return (
    <div>
      <p>Students</p>
      {students.length > 0 && <div className='student-list' >
        {students.map((student) => (
          <div key={student} className='student-hover' onClick={() => removeStudent(student)}>
            <OverlayTrigger
              key='top'
              placement='top'
              overlay={
                <Tooltip id='tooltip-top'>
                  Click to remove student
                </Tooltip>
              }
            >
              <p>{student};</p>
            </OverlayTrigger>
          </div>
        ))}
      </div>}
      <div className='add-student'>
        <Form.Control type='email' placeholder='Enter student email or username' value={student} onChange={(e) => setStudent(e.target.value)} />
        <Button variant='outline-secondary' type='button' onClick={() => addStudent()}>Add</Button>
      </div>
    </div>
  )
}

export default Terms