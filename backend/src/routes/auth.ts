import express from 'express';

const router = express.Router();

// Simple local authentication
router.post('/login', (req, res) => {
  // For local development, always succeed
  res.json({
    success: true,
    user: {
      id: 'local-user',
      username: 'test-user'
    }
  });
});

router.post('/logout', (req, res) => {
  res.json({ success: true });
});

router.get('/user', (req, res) => {
  // Return test user info
  res.json({
    success: true,
    user: {
      id: 'local-user',
      username: 'test-user'
    }
  });
});

export default router;
