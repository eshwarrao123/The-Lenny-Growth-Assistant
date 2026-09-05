// Next.js runs PostCSS from its own worker where Tailwind's automatic config
// search can miss tailwind.config.js (resolved against the worker's CWD), so
// point the plugin at the config explicitly via an absolute path.
const path = require('path')

module.exports = {
  plugins: {
    tailwindcss: { config: path.join(__dirname, 'tailwind.config.js') },
    autoprefixer: {},
  },
}



