import React from "react";
import Button from "react-bootstrap/Button";

const Rate: React.FC = () => {
    const handleRate = () => {
        console.log("Rate button clicked");
        // Link Flask API
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
