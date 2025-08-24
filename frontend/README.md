# Leave Management System - Frontend

A modern, responsive React application for managing employee leave requests. Built with React 19, Tailwind CSS, and React Router.

## Features

- **User Authentication**: Login and registration system with protected routes
- **Dashboard**: Overview of leave statistics, recent requests, and quick actions
- **Leave Request Management**: Submit new leave requests with comprehensive forms
- **Leave History**: View and filter all leave requests with search and sorting
- **Responsive Design**: Mobile-first design that works on all devices
- **Modern UI**: Clean, intuitive interface with smooth animations

## Pages

1. **Login** (`/login`) - User authentication
2. **Register** (`/register`) - New user registration
3. **Dashboard** (`/`) - Main dashboard with overview
4. **Submit Leave Request** (`/submit-leave`) - Create new leave requests
5. **My Leave Requests** (`/my-leaves`) - View and manage leave history

## Technology Stack

- **React 19** - Modern React with hooks and functional components
- **React Router 7** - Client-side routing and navigation
- **Tailwind CSS 3** - Utility-first CSS framework
- **Vite** - Fast build tool and development server
- **Context API** - State management for authentication

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.jsx      # Main layout with navigation
├── contexts/           # React contexts
│   └── AuthContext.jsx # Authentication state management
├── pages/              # Page components
│   ├── Dashboard.jsx
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── SubmitLeaveRequest.jsx
│   └── MyLeaveRequests.jsx
├── App.jsx             # Main app component with routing
├── main.jsx            # Entry point
└── index.css           # Global styles and Tailwind imports
```

## Features in Detail

### Authentication System
- Mock authentication using localStorage
- Protected routes for authenticated users
- Automatic redirect to login for unauthenticated users

### Leave Request Types
- Annual Leave
- Sick Leave
- Personal Leave
- Maternity Leave
- Paternity Leave
- Bereavement Leave

### Form Validation
- Client-side validation for all forms
- Real-time error feedback
- Required field validation
- Date range validation

### Responsive Design
- Mobile-first approach
- Collapsible navigation menu
- Adaptive grid layouts
- Touch-friendly interface

## Customization

### Styling
The application uses Tailwind CSS for styling. You can customize:
- Color scheme in `tailwind.config.js`
- Custom CSS in `src/index.css`
- Component-specific styles inline

### Data
Currently uses mock data. To integrate with your backend:
1. Replace mock API calls in components
2. Update data structures to match your API
3. Implement proper error handling

### Authentication
The current authentication is mocked. To implement real authentication:
1. Replace mock login/register functions in `AuthContext.jsx`
2. Implement proper token management
3. Add refresh token logic
4. Implement proper logout and session expiry

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

### Code Style
- Functional components with hooks
- Consistent naming conventions
- Proper TypeScript-like prop validation
- Clean, readable code structure

### Performance
- Lazy loading for routes (can be implemented)
- Optimized re-renders with proper dependency arrays
- Efficient state management
- Minimal bundle size with Vite

## Contributing

1. Follow the existing code style
2. Add proper error handling
3. Test on multiple devices and browsers
4. Update documentation for new features

## License

This project is part of the Leave Management System.

## Support

For issues or questions, please refer to the main project documentation.
