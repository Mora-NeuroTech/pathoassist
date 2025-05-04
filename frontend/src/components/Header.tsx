import React from 'react';

const Header: React.FC = () => {
    return (
        <header className="bg-white shadow-sm">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center">
                    <svg
                        className="w-8 h-8 text-primary-600 mr-3"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
                    </svg>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">PathoAssist</h1>
                        <p className="text-sm text-gray-600">Microscope Image Analysis</p>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;