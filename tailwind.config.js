module.exports = {
    content: [
        './src/templates/**/*.{html,js}', // Scan all HTML and JS files in your project
    ],
    theme: {
        container: {
            center: true,
        },
        extend: {
            boxShadow: {
                'inset-bharat': '10 10 -10 1px rgba(255, 255, 255, 0.1)',
            },
            colors: {
                customBlue: '#1e40af',
            },
        },
    },
};
