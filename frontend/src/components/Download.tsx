import React, { useState } from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface RateProps {
    modelID: string;
}

const Download: React.FC<RateProps> = ({ modelID }) => {
    const handleDownload = async () => {
        try {
            const res = await fetch(`${API_BASE}/download/${modelID}`);
            if (!res.ok) {
                console.error("Failed to download:", await res.text());
                return;
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${modelID}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading model:", error);
        }
    };

    return (
        <Button 
            variant="success"
            onClick={handleDownload}
        >
            Download Model
        </Button>
    );
};

export default Download;
