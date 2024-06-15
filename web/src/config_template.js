const config = {
    api: {
        host: "localhost", // Overwrite this with the IP address of your API server
        port: 1234
    },
};

const api_url = `http://${config.api.host}:${config.api.port}`;

export default config;
export { api_url };
