# RediLens
<img width="1360" height="635" alt="image" src="https://github.com/user-attachments/assets/06b82d60-041a-4edc-82ad-a201e374ddc9" />

RediLens is a web-based Redis GUI designed to provide a clean, modern, and user-friendly interface for developers and database administrators. It offers real-time performance monitoring, intuitive key management, and historical data analysis, all wrapped in a beautifully designed and responsive interface built with the latest web technologies.

## ✨ Key Features

  * **📊 Real-Time Dashboard:** Monitor key Redis metrics like Memory Usage, Operations per Second, and Hit Rate with live-updating charts.
  * **🔑 Comprehensive Key Management:** Browse, search, and manage your keys with a clean, paginated table. View, create, and delete keys through an intuitive UI.
  * **📜 Historical Analysis:** Explore historical performance trends with an interactive chart, allowing you to select and analyze data over various timeframes.
  * **⚙️ Server Overview:** Get an at-a-glance summary of your Redis server's configuration and health, including version, uptime, connected clients, and more.
  * **🎨 Modern UI/UX:** Built with `shadcn/ui` and Tailwind CSS, featuring a stunning dark mode, a collapsible sidebar, and a fully responsive design.
  * **🔧 Configurable:** Easily configure the data polling interval or disable it completely from the settings page.

## 🚀 Tech Stack

This project is built with a modern frontend stack:

  * **Framework:** [React](https://reactjs.org/)
  * **Language:** [TypeScript](https://www.typescriptlang.org/)
  * **Build Tool:** [Vite](https://vitejs.dev/)
  * **Styling:** [Tailwind CSS](https://tailwindcss.com/)
  * **UI Components:** [shadcn/ui](https://ui.shadcn.com/)
  * **Data Fetching & State Management:** [TanStack Query (React Query)](https://tanstack.com/query/)
  * **Charting:** [Recharts](https://recharts.org/)
  * **Routing:** [React Router](https://reactrouter.com/)
  * **Icons:** [Lucide React](https://lucide.dev/)

## 🏁 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

  * Node.js (v18 or later)
  * npm, yarn, or pnpm
  * A running Redis instance
  * The RediLens backend server running locally

### Installation & Setup

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/nickravesh/RediLens.git
    cd RediLens/frontend
    ```

2.  **Install dependencies:**

    ```sh
    npm install
    ```

3.  **Configure your environment:**
    Create a `.env.local` file in the `frontend` directory and add the URL of your backend API.

    ```env
    # .env.local
    VITE_API_BASE_URL=http://localhost:8000
    ```

4.  **Run the development server:**

    ```sh
    npm run dev
    ```

    Open [http://localhost:5173](https://www.google.com/search?q=http://localhost:5173) (or your specified port) to view it in the browser.

## 📄 License

This project is open source and distributed under the **GNU General Public License v3.0**. See `LICENSE` for more information.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please feel free to fork the repo and create a pull request. You can also open an issue with the tag "enhancement" to suggest a new feature.
