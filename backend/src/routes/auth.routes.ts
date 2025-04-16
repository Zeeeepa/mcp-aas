import { Router } from 'express';
import { register, login, getProfile } from '../controllers/auth.controller';
import { authenticateJwt, authenticateLocal } from '../services/auth.service';

const router = Router();

router.post('/register', register);
router.post('/login', authenticateLocal, login);
router.get('/profile', authenticateJwt, getProfile);

export default router;
