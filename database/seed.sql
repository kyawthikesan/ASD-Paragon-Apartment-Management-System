--Student Name: Nang Phwe Hleng Hun
--Student ID: 24043841
--Module: UFCF8S-30-2 Advanced Software Development

INSERT INTO locations (city, office_name) VALUES
('Bristol', 'Bristol Office'),
('Cardiff', 'Cardiff Office'),
('London', 'London HQ'),
('Manchester', 'Manchester Office');

-- =========================
-- TENANTS DATA
-- =========================

DELETE FROM tenants;

INSERT INTO tenants (name, NI_number, phone, email) VALUES
('John Smith', 'NI001', '07123456789', 'john.smith@email.com'),
('Emma Brown', 'NI002', '07234567890', 'emma.brown@email.com'),
('Liam Wilson', 'NI003', '07345678901', 'liam.wilson@email.com'),
('Olivia Taylor', 'NI004', '07456789012', 'olivia.taylor@email.com'),
('Noah Johnson', 'NI005', '07567890123', 'noah.johnson@email.com'),
('Ava Davies', 'NI006', '07678901234', 'ava.davies@email.com'),
('William Evans', 'NI007', '07789012345', 'william.evans@email.com'),
('Sophia Thomas', 'NI008', '07890123456', 'sophia.thomas@email.com'),
('James Roberts', 'NI009', '07901234567', 'james.roberts@email.com'),
('Isabella Lewis', 'NI010', '07012345678', 'isabella.lewis@email.com');

INSERT INTO apartments (location_id, type, rent, rooms) VALUES
-- Bristol
(1, 'Studio', 450, 1),
(1, '1BHK', 650, 2),

-- Cardiff
(2, 'Studio', 400, 1),
(2, '2BHK', 900, 3),

-- London (more expensive)
(3, '1BHK', 1200, 2),
(3, '2BHK', 1800, 3),

-- Manchester
(4, 'Studio', 500, 1),
(4, '3BHK', 1300, 4);


