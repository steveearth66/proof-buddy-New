import React, { useEffect, useState } from 'react'
import MainLayout from '../layouts/MainLayout';
import Container from 'react-bootstrap/Container';
import { useAuth } from '../context/AuthContext';
import termService from '../services/termServices';
import { useLocation } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import '../scss/_terms.scss';
import Button from 'react-bootstrap/esm/Button';
import Form from 'react-bootstrap/Form';
import { toast } from 'react-toastify';

function Term() {
    const location = useLocation();
    const [term, setTerm] = useState(location.state);
    const [assignments, setAssignments] = useState([]);
    const [showAssignmentCreate, setShowAssignmentCreate] = useState(false);
    const { id } = useParams();
    const { user } = useAuth();

    const removeStudent = async (email) => {
        try {
            await termService.removeStudent({ student: email, term: id });
            setTerm((prev) => ({ ...prev, students: prev.students.filter((student) => student.email !== email) }));
            toast.success('Student removed successfully');
        } catch (error) {
            console.error('Error removing student:', error);
            toast.error('Error removing student');
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const assignments = await termService.getAssignments(id || term?.id);
                const fetchedTerm = await termService.getTerm(id || term?.id);
                setAssignments(assignments);
                setTerm(fetchedTerm);
            } catch (error) {
                console.error('Error fetching assignments:', error);
            }
        };
        fetchData();
    }, [term?.id, id]);

    return (
        <MainLayout>
            <Container>
                {showAssignmentCreate && <CreateAssignment setAssignments={setAssignments} toggleShowCreate={setShowAssignmentCreate} />}
                <div className='term-head'>
                    <h2>{term?.name}</h2>
                    <p><b>Instructor: </b>{term?.instructor?.first_name} {term?.instructor?.last_name}</p>
                </div>
                <div className='term-layout'>
                    <div className='assignment-layout'>
                        <div className='headers'>
                            <h2>Assignments</h2>
                            {!user?.is_student && <Button variant='outline-secondary' onClick={() => setShowAssignmentCreate(true)}>Add Assignment</Button>}
                        </div>
                        <div className='assignment-container'>
                            {assignments.map((assignment) => (
                                <AssignmentCard key={assignment.id} assignment={assignment} />
                            ))}
                        </div>
                    </div>
                    <StudentList students={term?.students || []} isStudent={user?.is_student} removeStudent={removeStudent} />
                </div>
            </Container>
        </MainLayout>
    )
}

function AssignmentCard({ assignment }) {
    return (
        <div className='assignment-card'>
            <h2><b>{assignment.title}</b></h2>
            <h3>Description</h3>
            <p>{assignment.description}</p>
            <p><b>Due Date: </b>{assignment.due_date}</p>
            <Button variant='outline-primary'>View</Button>
        </div>
    )
}

function StudentList({ students, isStudent, removeStudent }) {
    return (
        <div className='student-layout'>
            <div className='headers'>
                <h2>Students</h2>
                {!isStudent && <Button variant='outline-secondary'>Add Student</Button>}
            </div>
            <div className='student-container'>
                {students.map((student) => (
                    <StudentCard key={student.id} student={student} isStudent={isStudent} removeStudent={removeStudent} />
                ))}
            </div>
        </div>
    )
}

function StudentCard({ student, isStudent, removeStudent }) {
    return (
        <div className='student-card'>
            <p className='name'>{student.first_name} {student.last_name}</p>
            <p><b>Email: </b>{student.email}</p>
            {!isStudent && <Button variant='outline-danger' onClick={() => removeStudent(student.email)}>Remove</Button>}
        </div>
    )
}

function CreateAssignment({ setAssignments, toggleShowCreate }) {
    const { id } = useParams();
    const handleSubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        const assignment = {
            title: form[0].value,
            description: form[1].value,
            due_date: form[2].value,
            term: id
        };
        try {
            const createdAssignment = await termService.createAssignment(assignment);
            setAssignments((prev) => [...prev, createdAssignment]);
            toast.success('Assignment created successfully');
            toggleShowCreate((prev) => !prev);
        } catch (error) {
            console.error('Error creating assignment:', error);
            toast.error('Error creating assignment');
        }
    }

    return (
        <div className='overlay'>
            <div className='term-card'>
                <h2>Create Assignment</h2>
                <Form onSubmit={handleSubmit}>
                    <Form.Group>
                        <Form.Label>Title</Form.Label>
                        <Form.Control type='text' placeholder='Assignment Title' />
                    </Form.Group>
                    <Form.Group>
                        <Form.Label>Description</Form.Label>
                        <Form.Control as='textarea' rows={8} placeholder='Assignment Description' />
                    </Form.Group>
                    <Form.Group>
                        <Form.Label>Due Date</Form.Label>
                        <Form.Control type='date' />
                    </Form.Group>
                    <div className='button-group'>
                        <Button variant='outline-danger' type='button' onClick={() => toggleShowCreate(false)}>Cancel</Button>
                        <Button variant='outline-primary' type='submit'>Create</Button>
                    </div>
                </Form>
            </div>
        </div>
    )
}

export default Term