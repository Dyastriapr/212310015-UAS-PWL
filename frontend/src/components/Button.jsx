import React from 'react';

const Button = ({ text, icon, paddingX = 'px-4', paddingY = 'py-2', fullWidth = false, onClick }) => {
  return (
    <button
      type="submit"  // Pastikan ini diatur ke "submit"
      onClick={onClick}
      className={`bg-primary mt-6 text-white font-bold ${paddingY} ${paddingX} rounded flex items-center justify-center ${fullWidth ? 'w-9/12' : 'w-auto'} mx-auto`}
    >
      {icon && <img src={icon} alt="Icon" className="w-6 h-6 mr-2" />}
      {text}
    </button>
  );
}

export default Button;
