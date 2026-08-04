
CREATE TABLE IF NOT EXISTS public.treat_packages (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    price NUMERIC NOT NULL,
    bonus INTEGER DEFAULT 0,
    price_per_treat NUMERIC,
    price_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.treat_packages ENABLE ROW LEVEL SECURITY;

-- Allow read access to all users
CREATE POLICY "Allow read access for all" ON public.treat_packages
    FOR SELECT USING (TRUE);

-- Allow admin access (if needed, currently allowing read for all)
-- For this MVP, we'll manually seed it.

INSERT INTO public.treat_packages (id, name, amount, price, bonus, price_per_treat, price_id)
VALUES 
('small', 'Tiny Snack', 10, 49, 0, 4.90, NULL),
('medium', 'Fishy Feast', 35, 129, 5, 3.68, NULL),
('large', 'Meaty Banquet', 125, 399, 25, 3.19, NULL),
('legendary', 'Royal Buffet', 650, 1499, 150, 2.30, NULL)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    amount = EXCLUDED.amount,
    price = EXCLUDED.price,
    bonus = EXCLUDED.bonus,
    price_per_treat = EXCLUDED.price_per_treat;

