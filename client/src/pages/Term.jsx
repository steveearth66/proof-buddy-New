import React, { useEffect, useState } from 'react'
import MainLayout from '../layouts/MainLayout';
import Container from 'react-bootstrap/Container';
import { useAuth } from '../context/AuthContext';
import termService from '../services/termServices';
import { useLocation } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import '../scss/_terms.scss';
import Button from 'react-bootstrap/esm/Button';

function Term() {
    const location = useLocation();
    const [term, setTerm] = useState(location.state);
    const [assignments, setAssignments] = useState([]);
    const { id } = useParams();
    const { user } = useAuth();

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
                <div className='term-head'>
                    <h2>{term?.name}</h2>
                    <p><b>Instructor: </b>{term?.instructor?.first_name} {term?.instructor?.last_name}</p>
                </div>
                <div className='term-layout'>
                    <div className='assignment-layout'>
                        <div className='headers'>
                            <h2>Assignments</h2>
                            {!user.is_student && <Button variant='outline-secondary'>Add Assignment</Button>}
                        </div>
                        <div className='assignment-container'>
                            {assignments.map((assignment) => (
                                <AssignmentCard key={assignment.id} assignment={assignment} />
                            ))}
                        </div>
                    </div>
                    <StudentList students={term?.students || []} isStudent={user.is_student} />
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

function StudentList({ students, isStudent }) {
    return (
        <div className='student-layout'>
            <div className='headers'>
                <h2>Students</h2>
                {!isStudent && <Button variant='outline-secondary'>Add Student</Button>}
            </div>
            <div className='student-container'>
                {students.map((student) => (
                    <StudentCard key={student.id} student={student} isStudent={isStudent} />
                ))}
            </div>
        </div>
    )
}

function StudentCard({ student, isStudent }) {
    return (
        <div className='student-card'>
            <p className='name'>{student.first_name} {student.last_name}</p>
            <p><b>Email: </b>{student.email}</p>
            {!isStudent && <Button variant='outline-danger'>Remove</Button>}
        </div>
    )
}

export default Term