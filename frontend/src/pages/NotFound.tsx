import React from 'react';
import { Link } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';

const NotFound: React.FC = () => {
  return (
    <PageLayout>
      <div style={{ textAlign: 'center', marginTop: '40px' }}>
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for does not exist.</p>
        <div style={{ marginTop: '20px' }}>
          <Link to="/">
            <button>Go to Home</button>
          </Link>
        </div>
      </div>
    </PageLayout>
  );
};

export default NotFound;

