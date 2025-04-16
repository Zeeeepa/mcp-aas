import { Router } from 'express';
import jwt from 'jsonwebtoken';

const router = Router();

// Simple in-memory user store for development
const testUser = {
  id: 'test-user-id',
  username: 'test@example.com',
  password: 'test123', // In production, this would be hashed
};

router.post('/login', (req, res) => {
  const { username, password } = req.body;

  // Auto-login for development
  const token = jwt.sign(
    { userId: testUser.id, username: testUser.username },
    'dev-secret-key',
    { expiresIn: '24h' }
  );

  res.json({
    token,
    user: {
      id: testUser.id,
      username: testUser.username,
    },
  });
});

router.post('/logout', (req, res) => {
  // In development, we don't need to do anything
  res.json({ success: true });
});

export const authRoutes = router;
