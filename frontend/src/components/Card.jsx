import React from 'react';

const Card = () => {
    return (
        <div className="w-full container mt-10 mb-10 flex items-center justify-center">
            <div className="p-10 bg-white rounded-lg shadow-lg">
                <h1 className="text-xl font-bold text-gray-900 mb-6">Bagaimana Cara Mengonversi Format Skripsi ke Jurnal ?</h1>
                <ol className="list-decimal list-inside space-y-4 text-lg">
                    <li>Klik "Pilih File" pada unggah skripsi dan pilih file skripsimu</li>
                    <li>Klik "Konversi" untuk memulai mengonversi</li>
                    <li>Tunggu sekitar 2-3 Menit</li>
                    <li>Ketika sudah selesai “Download”</li>
                </ol>
            </div>
        </div>
    );
};

export default Card;
