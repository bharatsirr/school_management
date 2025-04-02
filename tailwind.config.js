module.exports = {
    content: [
        './src/templates/**/*.{html,js}',  // Make sure the templates are being scanned
    ],
    theme: {
        container: {
            center: true,
        },
        extend: {
            boxShadow: {
                'inset-bharat': '10px 10px -10px 1px rgba(255, 255, 255, 0.1)',
            },
            colors: {
                customBlue: '#1e40af',
            },
        },
    },
};
