import React from "react";
import Button from "react-bootstrap/Button";

interface RateProps {
    artifactID: string;
    result: (data: any) => void;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Rate: React.FC<RateProps> = ({ artifactID, result }) => {
    const handleRate = async () => {
        try {
            const endpoint = `${API_BASE}/artifact/model/${artifactID}/rate`;
            const res = await fetch(endpoint, {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });
            const data = await res.json();
            result(data);
        } catch (error) {
            console.error("Error rating model:", error);
        }
    };

    return (
        <Button 
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
            onClick={handleRate}
        >
            Rate Model
        </Button>
    );
};

export default Rate;
