import 'bootstrap/dist/css/bootstrap.min.css';
import Health from './components/Health';
import Artifacts from './components/Artifacts';
import Reset from './components/Reset';

function App() {

    return (
        <div className="min-h-screen flex flex-col items-center bg-gray-300 px-6 py-8">
            {/* <h1 className="text-4xl font-bold text-gray-800 text-center mb-8">Registry Dashboard</h1> */}
            <div className="w-full relative mb-8">
                <h1 className="text-4xl font-bold text-center text-gray-800 w-full">
                    Registry Dashboard
                </h1>

                <div className="absolute top-0 right-0">
                    <Reset />
                </div>
            </div>

            {/* Health and Artifact Column Components */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mb-8">
                <Health />
                <Artifacts />
            </div>
        </div>
    );
}

export default App;
