import React, { useState } from "react";
import {Button, Modal, Form} from "react-bootstrap";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Reset: React.FC = () => {
    const [show, setShow] = useState<boolean>(false);
    const [password, setPassword] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);

    const handleClose = () => {
        setShow(false);
        setPassword("");
        setError("");
    }
    const handleShow = () => setShow(true);

    const handleReset = async () => {
        setLoading(true);
        setError("");

        try {
            const res = await fetch(`${API_BASE}/reset`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ password }),
            })
            if (res.status === 401) {
                setError("Invalid password.");
                return;
            }
            if (!res.ok) {
                setError("Error resetting registry.");
                return;
            }

            alert("Registry reset.");
            handleClose();
        } catch (e: any) {
            setError(e?.message || "Error resetting registry.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Button
                variant="danger"
                onClick={handleShow}
            >
                Reset Registry
            </Button>

            <Modal
                show={show}
                onHide={handleClose}
                centered
            >
                <Modal.Header closeButton>
                    <Modal.Title>Reset Registry</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    <p>Enter admin password to reset registry</p>
                    <Form.Control
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    {error && (
                        <p style={{ color: "red", marginTop: "10px" }}>
                            {error}
                        </p>
                    )}
                </Modal.Body>

                <Modal.Footer>
                    <Button
                        variant="secondary"
                        onClick={handleClose}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        disabled={loading}
                        onClick={handleReset}
                    >
                        {loading ? "Resetting..." : "Confirm Reset"}
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default Reset;
