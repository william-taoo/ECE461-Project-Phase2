import React, { useState } from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Reset: React.FC = () => {
    const handleReset = async () => {
        try {
            const res = await fetch(`${API_BASE}/reset`, {
                method: "DELETE",
            })
            if (res.status === 401) {
                console.log("Unauthorized");
                return;
            }
            if (!res.ok) {
                console.log("Error resetting registry");
                return;
            }

            alert("Registry reset.");
        } catch (e: any) {
            console.log(e);
        }
    };

    return (
        <Button
            variant="danger"
            onClick={handleReset}
            data-testid="reset-button"
        >
            Reset Registry
        </Button>
    );
};

export default Reset;
