import React, { useEffect, useState } from 'react'
import MainLayout from '../layouts/MainLayout';
import Container from 'react-bootstrap/Container';
import { useAuth } from '../context/AuthContext';
import termService from '../services/termServices';
import { useLocation } from 'react-router-dom';
import { useParams } from 'react-router-dom';

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
                <h1>{term?.name}</h1>
            </Container>
        </MainLayout>
    )
}

export default Term