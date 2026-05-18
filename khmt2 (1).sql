-- =====================================================
-- PET HOTEL DATABASE SCHEMA - FIXED VERSION v3
-- Timeline: 2026-02-19 to 2026-05-19 (90 days)
-- Fix: Added rooms 11-63 to support 1500 non-overlapping bookings
--   Room capacity per type (3-day stays, 90-day window = 30 slots/room):
--     Type 1 Small Dog  (rooms  1-2  + 11-34) = 24 rooms → 720 slots
--     Type 2 Medium Dog (rooms  3-4  + 35-41) =  7 rooms → 210 slots
--     Type 3 Large Dog  (rooms  5-7  + 42-45) =  4 rooms → 120 slots
--     Type 4 Cat        (rooms  8-9  + 46-63) = 18 rooms → 540 slots
-- =====================================================

CREATE DATABASE IF NOT EXISTS PetHotel;
USE PetHotel;

-- =====================================================
-- 1. BẢNG DANH MỤC
-- =====================================================

CREATE TABLE booking_statuses (
    status_id    INT AUTO_INCREMENT PRIMARY KEY,
    status_name  VARCHAR(20)  NOT NULL UNIQUE,
    display_order INT         DEFAULT 0,
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO booking_statuses (status_id, status_name, display_order) VALUES
(1, 'booked',      1),
(2, 'checked_in',  2),
(3, 'completed',   3),
(4, 'cancelled',   4);

CREATE TABLE payment_methods (
    method_id   INT AUTO_INCREMENT PRIMARY KEY,
    method_name VARCHAR(20)   NOT NULL UNIQUE,
    is_active   BIT           DEFAULT 1,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO payment_methods (method_id, method_name) VALUES
(1, 'cash'),
(2, 'transfer'),
(3, 'card');

CREATE TABLE subscription_statuses (
    status_id   INT AUTO_INCREMENT PRIMARY KEY,
    status_name VARCHAR(20)   NOT NULL UNIQUE
);

INSERT INTO subscription_statuses (status_id, status_name) VALUES
(1, 'active'),
(2, 'expired'),
(3, 'cancelled'),
(4, 'upgraded');

CREATE TABLE plan_types (
    plan_type_id     INT AUTO_INCREMENT PRIMARY KEY,
    plan_name        VARCHAR(50)     NOT NULL,
    discount_percent DECIMAL(5,2)    DEFAULT 0,
    min_points       INT             DEFAULT 0,
    max_points       INT             NULL,
    is_active        BIT             DEFAULT 1,
    created_at       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO plan_types (plan_type_id, plan_name, discount_percent, min_points) VALUES
(1, 'Standard', 0,  0),
(2, 'Silver',   5,  1000),
(3, 'Gold',     10, 5000),
(4, 'Platinum', 15, 20000);

CREATE TABLE service_catalog (
    service_type_id INT AUTO_INCREMENT PRIMARY KEY,
    service_type    VARCHAR(50)     NOT NULL UNIQUE,
    base_price      DECIMAL(18,0)   NOT NULL CHECK (base_price >= 0),
    unit            VARCHAR(20)     DEFAULT 'lần',
    is_active       BIT             DEFAULT 1,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO service_catalog (service_type_id, service_type, base_price, unit) VALUES
(1, 'grooming',  150000, 'lần'),
(2, 'daycare',   100000, 'ngày'),
(3, 'pickup',     50000, 'lượt'),
(4, 'dropoff',    50000, 'lượt'),
(5, 'swimming',   80000, 'lần'),
(6, 'walk',       60000, 'lần');

-- =====================================================
-- 2. EMPLOYEES
-- =====================================================

CREATE TABLE employees (
    employee_id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name            VARCHAR(100)    NOT NULL,
    role                 VARCHAR(20)     NOT NULL CHECK (role IN ('manager','fulltime','parttime')),
    phone                VARCHAR(15)     NOT NULL UNIQUE,
    base_salary_per_hour DECIMAL(18,0)   NOT NULL CHECK (base_salary_per_hour >= 0),
    is_active            BIT             DEFAULT 1
);

-- =====================================================
-- 3. CUSTOMERS
-- =====================================================

CREATE TABLE customers (
    customer_id      INT AUTO_INCREMENT PRIMARY KEY,
    full_name        VARCHAR(100)    NOT NULL,
    phone            VARCHAR(15)     NOT NULL UNIQUE,
    address          VARCHAR(255)    NULL,
    district         VARCHAR(50)     NULL,
    join_date        DATE            NOT NULL DEFAULT (CURRENT_DATE),
    last_active_date DATE            NULL,
    total_spent      DECIMAL(18,0)   DEFAULT 0,
    historical_flag  BIT             DEFAULT 0,

    CONSTRAINT chk_customer_phone CHECK (CHAR_LENGTH(phone) >= 10)
);

-- =====================================================
-- 4. PETS
-- =====================================================

CREATE TABLE pets (
    pet_id              INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT             NOT NULL,
    pet_name            VARCHAR(100)    NOT NULL,
    species             VARCHAR(20)     NOT NULL CHECK (species IN ('dog','cat')),
    breed               VARCHAR(100)    NULL,
    weight              DECIMAL(5,2)    NOT NULL CHECK (weight > 0),
    age                 INT             NULL CHECK (age >= 0),
    gender              VARCHAR(10)     NULL,
    sterilized          BIT             DEFAULT 0,
    health_condition    VARCHAR(500)    NULL,
    vaccinated          BIT             DEFAULT 0,
    behaviour_note      VARCHAR(500)    NULL,
    special_requirement VARCHAR(500)    NULL,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- =====================================================
-- 5. ROOM TYPES
-- =====================================================

CREATE TABLE room_types (
    room_type_id    INT AUTO_INCREMENT PRIMARY KEY,
    type_name       VARCHAR(100)    NOT NULL,
    species         VARCHAR(20)     NOT NULL CHECK (species IN ('dog','cat','both')),
    min_weight      DECIMAL(5,2)    NOT NULL DEFAULT 0,
    max_weight      DECIMAL(5,2)    NOT NULL,
    price_per_night DECIMAL(18,0)   NOT NULL CHECK (price_per_night >= 0),

    CONSTRAINT chk_room_weight CHECK (min_weight < max_weight)
);

INSERT INTO room_types (room_type_id, type_name, species, min_weight, max_weight, price_per_night) VALUES
(1, 'Small Dog Room',  'dog',  0,  5,   150000),
(2, 'Medium Dog Room', 'dog',  5,  15,  250000),
(3, 'Large Dog Room',  'dog',  15, 50,  400000),
(4, 'Cat Room',        'cat',  0,  10,  120000),
(5, 'Family Room',     'both', 0,  100, 500000);

-- =====================================================
-- 6. ROOMS
-- =====================================================

CREATE TABLE rooms (
    room_id      INT AUTO_INCREMENT PRIMARY KEY,
    room_type_id INT             NOT NULL REFERENCES room_types(room_type_id),
    camera_url   VARCHAR(500)    NULL,
    is_active    BIT             DEFAULT 1
);

-- Original demo rooms (1-10)
INSERT INTO rooms (room_id, room_type_id) VALUES
(1,1),(2,1),(3,2),(4,2),(5,3),(6,3),(7,3),(8,4),(9,4),(10,5);

-- =====================================================
-- EXTENDED ROOMS for 1500 bulk bookings (no double-booking)
-- Slot capacity per room = FLOOR(90/3) = 30 bookings
--
-- Pet distribution from bulk data (1500 pets):
--   Cat        (MOD(n,3)=0):                       ~500  → need 18 cat rooms
--   Small Dog  (dog, weight 3, else branch):        ~685  → need 24 small rooms
--   Medium Dog (dog, weight 10, MOD(n,5)=0):        ~200  → need  7 medium rooms
--   Large Dog  (dog, weight 20, MOD(n,7)=0):        ~115  → need  4 large rooms
--
-- Room ID ranges assigned in insert_data_v5:
--   Small Dog  → rooms 11-34 (24 rooms, type 1)
--   Medium Dog → rooms 35-41 ( 7 rooms, type 2)
--   Large Dog  → rooms 42-45 ( 4 rooms, type 3)
--   Cat        → rooms 46-63 (18 rooms, type 4)
-- =====================================================

-- Type 1: Small Dog (rooms 11-34, 24 rooms)
INSERT INTO rooms (room_id, room_type_id) VALUES
(11,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),
(19,1),(20,1),(21,1),(22,1),(23,1),(24,1),(25,1),(26,1),
(27,1),(28,1),(29,1),(30,1),(31,1),(32,1),(33,1),(34,1);

-- Type 2: Medium Dog (rooms 35-41, 7 rooms)
INSERT INTO rooms (room_id, room_type_id) VALUES
(35,2),(36,2),(37,2),(38,2),(39,2),(40,2),(41,2);

-- Type 3: Large Dog (rooms 42-45, 4 rooms)
INSERT INTO rooms (room_id, room_type_id) VALUES
(42,3),(43,3),(44,3),(45,3);

-- Type 4: Cat (rooms 46-63, 18 rooms)
INSERT INTO rooms (room_id, room_type_id) VALUES
(46,4),(47,4),(48,4),(49,4),(50,4),(51,4),(52,4),(53,4),(54,4),
(55,4),(56,4),(57,4),(58,4),(59,4),(60,4),(61,4),(62,4),(63,4);

-- =====================================================
-- 7. BOOKINGS
-- =====================================================

CREATE TABLE bookings (
    booking_id        INT AUTO_INCREMENT PRIMARY KEY,
    customer_id       INT             NOT NULL,
    pet_id            INT             NOT NULL,
    room_id           INT             NOT NULL,
    check_in          DATETIME        NOT NULL,
    check_out         DATETIME        NOT NULL,
    booking_status_id INT             NOT NULL DEFAULT 1,
    room_price        DECIMAL(18,0)   DEFAULT 0,
    notes             VARCHAR(500)    NULL,

    CONSTRAINT chk_booking_dates CHECK (check_out > check_in),
    FOREIGN KEY (customer_id)       REFERENCES customers(customer_id),
    FOREIGN KEY (pet_id)            REFERENCES pets(pet_id),
    FOREIGN KEY (room_id)           REFERENCES rooms(room_id),
    FOREIGN KEY (booking_status_id) REFERENCES booking_statuses(status_id)
);

-- =====================================================
-- 8. BILLING
-- =====================================================

CREATE TABLE billing (
    payment_id        INT AUTO_INCREMENT PRIMARY KEY,
    booking_id        INT             NOT NULL UNIQUE REFERENCES bookings(booking_id),
    employee_id       INT             NULL REFERENCES employees(employee_id),
    total_amount      DECIMAL(18,0)   NOT NULL DEFAULT 0,
    discount_amount   DECIMAL(18,0)   DEFAULT 0,
    payment_date      DATETIME        NULL,
    payment_method_id INT             NULL REFERENCES payment_methods(method_id),
    notes             VARCHAR(500)    NULL
);

-- =====================================================
-- 9. SERVICES
-- =====================================================

CREATE TABLE services (
    service_id      INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT             NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    pet_id          INT             NOT NULL REFERENCES pets(pet_id),
    service_type_id INT             NOT NULL REFERENCES service_catalog(service_type_id),
    unit_price      DECIMAL(18,0)   NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    quantity        INT             NOT NULL DEFAULT 1 CHECK (quantity > 0),
    total_price     DECIMAL(18,0)   NOT NULL DEFAULT 0,
    service_date    DATE            NOT NULL DEFAULT (CURRENT_DATE),
    frequency_tag   VARCHAR(100)    NULL,
    notes           VARCHAR(500)    NULL,
    status          VARCHAR(10)     NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','done','cancelled'))
);

-- =====================================================
-- 10. ATTENDANCE
-- =====================================================

CREATE TABLE attendance (
    attendance_id  INT AUTO_INCREMENT PRIMARY KEY,
    employee_id    INT             NOT NULL REFERENCES employees(employee_id),
    work_date      DATE            NOT NULL DEFAULT (CURRENT_DATE),
    check_in       DATETIME        NOT NULL,
    check_out      DATETIME        NULL,
    working_hours  DECIMAL(5,2)    DEFAULT 0,
    overtime_hours DECIMAL(5,2)    DEFAULT 0,
    penalty        DECIMAL(18,0)   DEFAULT 0,
    note           VARCHAR(500)    NULL,

    CONSTRAINT chk_attendance_checkout
        CHECK (check_out IS NULL OR check_out > check_in)
);

-- =====================================================
-- 11. CUSTOMER POINTS
-- =====================================================

CREATE TABLE customer_points (
    customer_id     INT PRIMARY KEY,
    total_point     INT             NOT NULL DEFAULT 0 CHECK (total_point >= 0),
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    membership_type VARCHAR(20)     DEFAULT 'FREE',
    usable_points   INT             DEFAULT 0,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- =====================================================
-- 12. POINT TRANSACTIONS
-- =====================================================

CREATE TABLE point_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id    INT             NOT NULL REFERENCES customers(customer_id),
    booking_id     INT             NOT NULL REFERENCES bookings(booking_id),
    points         INT             NOT NULL CHECK (points != 0),
    description    VARCHAR(255)    NULL,
    created_at     DATETIME        DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 13. CUSTOMER SUBSCRIPTIONS
-- =====================================================

CREATE TABLE customer_subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT     NOT NULL REFERENCES customers(customer_id),
    plan_type_id    INT     NOT NULL REFERENCES plan_types(plan_type_id),
    start_date      DATE    NOT NULL,
    end_date        DATE    NOT NULL,
    status_id       INT     NOT NULL DEFAULT 1,

    CONSTRAINT chk_subscription_dates CHECK (end_date >= start_date),
    FOREIGN KEY (status_id) REFERENCES subscription_statuses(status_id)
);

-- =====================================================
-- 14. INDEXES
-- =====================================================

CREATE INDEX idx_bookings_daterange        ON bookings(check_in, check_out);
CREATE INDEX idx_bookings_customer_status  ON bookings(customer_id, booking_status_id);
CREATE INDEX idx_bookings_room_dates       ON bookings(room_id, check_in, check_out);
CREATE INDEX idx_bookings_status           ON bookings(booking_status_id);
CREATE INDEX idx_services_booking_type     ON services(booking_id, service_type_id);
CREATE INDEX idx_services_service_date     ON services(service_date);
CREATE INDEX idx_billing_payment_date      ON billing(payment_date);
CREATE INDEX idx_billing_booking           ON billing(booking_id);
CREATE INDEX idx_points_customer           ON point_transactions(customer_id, created_at);
CREATE INDEX idx_attendance_employee_date  ON attendance(employee_id, work_date);
CREATE INDEX idx_attendance_checkin        ON attendance(check_in);
CREATE INDEX idx_customers_phone           ON customers(phone);
CREATE INDEX idx_customers_join_date       ON customers(join_date);
CREATE INDEX idx_customers_last_active     ON customers(last_active_date);
CREATE INDEX idx_pets_customer             ON pets(customer_id);
CREATE INDEX idx_pets_species              ON pets(species);

-- =====================================================
-- 15. FUNCTIONS
-- =====================================================

DELIMITER //

CREATE FUNCTION calculate_nights(
    check_in  DATETIME,
    check_out DATETIME
)
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN CEIL(
        TIMESTAMPDIFF(SECOND, check_in, check_out) / 86400
    );
END //

CREATE FUNCTION calculate_booking_total_v2(p_booking_id INT)
RETURNS DECIMAL(18,0)
DETERMINISTIC
BEGIN
    DECLARE v_room_price     DECIMAL(18,0);
    DECLARE v_services_total DECIMAL(18,0);
    DECLARE v_nights         INT;
    DECLARE v_check_in       DATETIME;
    DECLARE v_check_out      DATETIME;

    SELECT check_in, check_out, IFNULL(room_price, 0)
    INTO v_check_in, v_check_out, v_room_price
    FROM bookings
    WHERE booking_id = p_booking_id;

    SET v_nights = calculate_nights(v_check_in, v_check_out);

    SELECT IFNULL(SUM(total_price), 0)
    INTO v_services_total
    FROM services
    WHERE booking_id = p_booking_id;

    RETURN v_room_price * v_nights + v_services_total;
END //

DELIMITER ;

-- =====================================================
-- 16. TRIGGERS
-- =====================================================

DELIMITER //

CREATE TRIGGER trg_calculate_working_hours
BEFORE UPDATE ON attendance
FOR EACH ROW
BEGIN
    IF NEW.check_out IS NOT NULL THEN
        SET NEW.working_hours  = TIMESTAMPDIFF(SECOND, NEW.check_in, NEW.check_out) / 3600;
        SET NEW.overtime_hours = GREATEST(0, NEW.working_hours - 8);
    END IF;
END //

CREATE TRIGGER trg_award_points_on_completion
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    DECLARE v_total    DECIMAL(18,0);
    DECLARE v_points   INT;
    DECLARE v_membership VARCHAR(20);

    IF NEW.booking_status_id = 3 AND OLD.booking_status_id <> 3 THEN
        SET v_total  = calculate_booking_total_v2(NEW.booking_id);
        SET v_points = FLOOR(v_total / 100000);

        SELECT membership_type INTO v_membership
        FROM customer_points
        WHERE customer_id = NEW.customer_id;

        IF v_membership IS NULL THEN
            INSERT INTO customer_points (customer_id, total_point, usable_points, membership_type)
            VALUES (NEW.customer_id, 0, 0, 'FREE');
        END IF;

        INSERT INTO point_transactions (customer_id, booking_id, points, description)
        VALUES (NEW.customer_id, NEW.booking_id, v_points,
                CONCAT('Reward points from booking #', NEW.booking_id));
    END IF;
END //

CREATE TRIGGER trg_validate_pet_room_compatibility
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM pets p
        INNER JOIN rooms r   ON r.room_id      = NEW.room_id
        INNER JOIN room_types rt ON r.room_type_id = rt.room_type_id
        WHERE p.pet_id = NEW.pet_id
          AND ((rt.species = 'dog' AND p.species <> 'dog')
            OR (rt.species = 'cat' AND p.species <> 'cat')
            OR (p.weight < rt.min_weight)
            OR (p.weight > rt.max_weight))
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Pet does not match room type';
    END IF;
END //

CREATE TRIGGER trg_validate_booking_status
BEFORE UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF OLD.booking_status_id <> NEW.booking_status_id THEN
        IF (OLD.booking_status_id IN (3, 4)
            OR (OLD.booking_status_id = 1 AND NEW.booking_status_id NOT IN (2, 4))
            OR (OLD.booking_status_id = 2 AND NEW.booking_status_id NOT IN (3, 4))) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid booking status transition';
        END IF;
    END IF;
END //

CREATE TRIGGER trg_prevent_double_booking
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM bookings b
        WHERE b.room_id = NEW.room_id
          AND b.booking_status_id IN (1, 2)
          AND b.check_in  < NEW.check_out
          AND b.check_out > NEW.check_in
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Room already booked for selected period';
    END IF;
END //

CREATE TRIGGER trg_set_service_price_snapshot
BEFORE INSERT ON services
FOR EACH ROW
BEGIN
    DECLARE v_base_price DECIMAL(18,0);

    SELECT base_price INTO v_base_price
    FROM service_catalog
    WHERE service_type_id = NEW.service_type_id;

    IF NEW.unit_price = 0 OR NEW.unit_price IS NULL THEN
        SET NEW.unit_price = v_base_price;
    END IF;

    SET NEW.total_price = NEW.unit_price * NEW.quantity;
END //

CREATE TRIGGER trg_prevent_overlapping_attendance
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM attendance a
        WHERE a.employee_id = NEW.employee_id
          AND a.check_in  < IFNULL(NEW.check_out, '9999-12-31')
          AND IFNULL(a.check_out, '9999-12-31') > NEW.check_in
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Overlapping attendance records';
    END IF;
END //

CREATE TRIGGER trg_set_billing_amount
BEFORE INSERT ON billing
FOR EACH ROW
BEGIN
    IF NEW.total_amount = 0 THEN
        SET NEW.total_amount = calculate_booking_total_v2(NEW.booking_id);
    END IF;
END //

CREATE TRIGGER trg_set_room_price_snapshot
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    DECLARE v_room_price DECIMAL(18,0);
    DECLARE v_discount   DECIMAL(5,2) DEFAULT 0;

    SELECT rt.price_per_night
    INTO v_room_price
    FROM rooms r
    INNER JOIN room_types rt ON r.room_type_id = rt.room_type_id
    WHERE r.room_id = NEW.room_id;

    SELECT IFNULL(pt.discount_percent, 0)
    INTO v_discount
    FROM customer_subscriptions cs
    INNER JOIN plan_types pt ON cs.plan_type_id = pt.plan_type_id
    WHERE cs.customer_id = NEW.customer_id
      AND cs.status_id   = 1
      AND cs.start_date  <= DATE(NEW.check_in)
      AND cs.end_date    >= DATE(NEW.check_in)
    ORDER BY pt.discount_percent DESC
    LIMIT 1;

    SET NEW.room_price = ROUND(IFNULL(v_room_price, 0) * (1 - v_discount / 100), 0);
END //

CREATE TRIGGER trg_update_customer_points
AFTER INSERT ON point_transactions
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM customer_points WHERE customer_id = NEW.customer_id) THEN
        UPDATE customer_points
        SET total_point = total_point + NEW.points
        WHERE customer_id = NEW.customer_id;
    ELSE
        INSERT INTO customer_points (customer_id, total_point, membership_type, usable_points)
        VALUES (NEW.customer_id, NEW.points, 'FREE', 0);
    END IF;
END //

CREATE TRIGGER trg_auto_upgrade_membership
AFTER INSERT ON point_transactions
FOR EACH ROW
BEGIN
    DECLARE v_total_points   INT;
    DECLARE v_new_plan_id    INT;
    DECLARE v_current_plan_id INT DEFAULT 0;

    SELECT total_point INTO v_total_points
    FROM customer_points WHERE customer_id = NEW.customer_id;

    SELECT plan_type_id INTO v_new_plan_id
    FROM plan_types
    WHERE min_points <= v_total_points AND is_active = 1
    ORDER BY min_points DESC LIMIT 1;

    SELECT IFNULL(plan_type_id, 0) INTO v_current_plan_id
    FROM customer_subscriptions
    WHERE customer_id = NEW.customer_id AND status_id = 1
    ORDER BY plan_type_id DESC LIMIT 1;

    IF v_new_plan_id > v_current_plan_id THEN
        UPDATE customer_subscriptions SET status_id = 4
        WHERE customer_id = NEW.customer_id AND status_id = 1;

        INSERT INTO customer_subscriptions (customer_id, plan_type_id, start_date, end_date, status_id)
        VALUES (NEW.customer_id, v_new_plan_id, CURRENT_DATE,
                DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR), 1);

        IF v_new_plan_id >= 2 THEN
            UPDATE customer_points
            SET usable_points   = usable_points + NEW.points,
                membership_type = (SELECT plan_name FROM plan_types WHERE plan_type_id = v_new_plan_id)
            WHERE customer_id = NEW.customer_id;
        END IF;
    ELSE
        UPDATE customer_points
        SET usable_points = usable_points + NEW.points
        WHERE customer_id = NEW.customer_id
          AND membership_type NOT IN ('FREE', 'Standard');
    END IF;
END //

CREATE TRIGGER trg_update_billing_on_services_insert
AFTER INSERT ON services
FOR EACH ROW
BEGIN
    UPDATE billing
    SET total_amount = calculate_booking_total_v2(NEW.booking_id)
    WHERE booking_id = NEW.booking_id AND payment_method_id IS NULL;
END //

CREATE TRIGGER trg_update_billing_on_services_update
AFTER UPDATE ON services
FOR EACH ROW
BEGIN
    UPDATE billing
    SET total_amount = calculate_booking_total_v2(NEW.booking_id)
    WHERE booking_id = NEW.booking_id AND payment_method_id IS NULL;
END //

CREATE TRIGGER trg_update_billing_on_services_delete
AFTER DELETE ON services
FOR EACH ROW
BEGIN
    UPDATE billing
    SET total_amount = calculate_booking_total_v2(OLD.booking_id)
    WHERE booking_id = OLD.booking_id AND payment_method_id IS NULL;
END //

DELIMITER ;

-- =====================================================
-- 17. STORED PROCEDURES
-- =====================================================

DELIMITER //

CREATE PROCEDURE use_points(
    IN p_customer_id INT,
    IN p_points      INT
)
BEGIN
    DECLARE v_membership    VARCHAR(20);
    DECLARE v_current_points INT;

    SELECT membership_type, usable_points
    INTO v_membership, v_current_points
    FROM customer_points WHERE customer_id = p_customer_id;

    IF v_membership = 'FREE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'FREE membership cannot use points';
    END IF;

    IF v_current_points < p_points THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough usable points';
    END IF;

    UPDATE customer_points
    SET usable_points = usable_points - p_points
    WHERE customer_id = p_customer_id;
END //

CREATE PROCEDURE process_payment(
    IN p_booking_id          INT,
    IN p_employee_id         INT,
    IN p_payment_method_name VARCHAR(20)
)
BEGIN
    DECLARE v_payment_method_id INT;
    DECLARE v_billing_id        INT;
    DECLARE v_total_amount      DECIMAL(18,0);
    DECLARE v_customer_id       INT;

    START TRANSACTION;

    SELECT method_id INTO v_payment_method_id
    FROM payment_methods WHERE method_name = p_payment_method_name LIMIT 1;

    IF v_payment_method_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment method';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM employees WHERE employee_id = p_employee_id AND is_active = 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid or inactive employee';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM bookings WHERE booking_id = p_booking_id AND booking_status_id = 3) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking not completed';
    END IF;

    IF EXISTS (SELECT 1 FROM billing WHERE booking_id = p_booking_id AND payment_method_id IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking already paid';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM billing WHERE booking_id = p_booking_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Billing record not found';
    END IF;

    UPDATE billing
    SET payment_method_id = v_payment_method_id,
        payment_date      = CURRENT_TIMESTAMP,
        employee_id       = p_employee_id
    WHERE booking_id = p_booking_id;

    SELECT bi.payment_id, bi.total_amount, b.customer_id
    INTO v_billing_id, v_total_amount, v_customer_id
    FROM billing bi INNER JOIN bookings b ON bi.booking_id = b.booking_id
    WHERE bi.booking_id = p_booking_id LIMIT 1;

    UPDATE customers
    SET total_spent      = total_spent + v_total_amount,
        last_active_date = CURRENT_DATE
    WHERE customer_id = v_customer_id;

    COMMIT;

    SELECT 1 AS success, 'Payment successful' AS message,
           v_billing_id AS payment_id, v_total_amount AS total_amount;
END //

CREATE PROCEDURE daily_maintenance()
BEGIN
    DECLARE v_expired_count INT DEFAULT 0;

    UPDATE customer_subscriptions SET status_id = 2
    WHERE status_id = 1 AND end_date < CURRENT_DATE;

    SET v_expired_count = ROW_COUNT();

    UPDATE customers c
    SET last_active_date = (
        SELECT MAX(DATE(b.check_in)) FROM bookings b
        WHERE b.customer_id = c.customer_id AND b.booking_status_id = 3
    )
    WHERE EXISTS (
        SELECT 1 FROM bookings b
        WHERE b.customer_id = c.customer_id AND b.booking_status_id = 3
    );

    SELECT v_expired_count AS expired_subscriptions;
END //

CREATE PROCEDURE sp_calculate_monthly_revenue(
    IN p_year  INT,
    IN p_month INT
)
BEGIN
    SELECT
        YEAR(payment_date)  AS year,
        MONTH(payment_date) AS month,
        COUNT(*)            AS total_transactions,
        SUM(total_amount)   AS total_revenue,
        SUM(CASE WHEN pm.method_name = 'cash'     THEN total_amount ELSE 0 END) AS cash_revenue,
        SUM(CASE WHEN pm.method_name = 'transfer' THEN total_amount ELSE 0 END) AS transfer_revenue,
        SUM(CASE WHEN pm.method_name = 'card'     THEN total_amount ELSE 0 END) AS card_revenue
    FROM billing b
    LEFT JOIN payment_methods pm ON b.payment_method_id = pm.method_id
    WHERE b.payment_method_id IS NOT NULL
      AND (p_year  IS NULL OR YEAR(payment_date)  = p_year)
      AND (p_month IS NULL OR MONTH(payment_date) = p_month)
    GROUP BY YEAR(payment_date), MONTH(payment_date)
    ORDER BY YEAR(payment_date) DESC, MONTH(payment_date) DESC;
END //

CREATE PROCEDURE sp_get_care_view(IN p_date DATE)
BEGIN
    IF p_date IS NULL THEN
        SET p_date = CURRENT_DATE;
    END IF;

    SELECT
        b.booking_id, p.pet_name, p.species, p.weight,
        p.health_condition, p.behaviour_note, p.special_requirement,
        r.room_id, rt.type_name AS room_type, r.camera_url,
        c.full_name AS owner_name, c.phone AS owner_phone,
        b.check_in, b.check_out,
        GROUP_CONCAT(DISTINCT sc.service_type SEPARATOR ', ') AS services_today
    FROM bookings b
    INNER JOIN pets p         ON b.pet_id      = p.pet_id
    INNER JOIN customers c    ON b.customer_id  = c.customer_id
    INNER JOIN rooms r        ON b.room_id      = r.room_id
    INNER JOIN room_types rt  ON r.room_type_id = rt.room_type_id
    LEFT JOIN services s      ON b.booking_id   = s.booking_id AND s.service_date = p_date
    LEFT JOIN service_catalog sc ON s.service_type_id = sc.service_type_id
    WHERE b.booking_status_id = 2
      AND DATE(b.check_in)  <= p_date
      AND DATE(b.check_out) > p_date
    GROUP BY b.booking_id, p.pet_name, p.species, p.weight,
             p.health_condition, p.behaviour_note, p.special_requirement,
             r.room_id, rt.type_name, r.camera_url,
             c.full_name, c.phone, b.check_in, b.check_out
    ORDER BY r.room_id;
END //

DELIMITER ;

-- =====================================================
-- 18. VIEWS
-- =====================================================

CREATE VIEW vw_monthly_revenue AS
SELECT
    CONCAT(YEAR(b.payment_date), '-', LPAD(MONTH(b.payment_date), 2, '0')) AS month_year,
    YEAR(b.payment_date)  AS year,
    MONTH(b.payment_date) AS month,
    COUNT(b.payment_id)   AS total_transactions,
    SUM(b.total_amount)   AS revenue_total,
    SUM(CASE WHEN pm.method_name = 'cash'     THEN b.total_amount ELSE 0 END) AS revenue_cash,
    SUM(CASE WHEN pm.method_name = 'transfer' THEN b.total_amount ELSE 0 END) AS revenue_transfer,
    SUM(CASE WHEN pm.method_name = 'card'     THEN b.total_amount ELSE 0 END) AS revenue_card,
    AVG(b.total_amount)   AS avg_booking_value
FROM billing b
LEFT JOIN payment_methods pm ON b.payment_method_id = pm.method_id
WHERE b.payment_method_id IS NOT NULL
GROUP BY YEAR(b.payment_date), MONTH(b.payment_date);

CREATE VIEW vw_service_revenue AS
SELECT sc.service_type,
       COUNT(*)            AS service_count,
       SUM(s.total_price)  AS total_revenue,
       AVG(s.total_price)  AS avg_price
FROM services s
INNER JOIN service_catalog sc ON s.service_type_id = sc.service_type_id
GROUP BY sc.service_type;

CREATE VIEW vw_customer_lifetime_value AS
SELECT
    c.customer_id, c.full_name, c.phone, c.join_date,
    COUNT(DISTINCT b.booking_id) AS total_bookings,
    c.total_spent                AS lifetime_value,
    cp.total_point               AS current_points,
    pt.plan_name                 AS current_membership
FROM customers c
LEFT JOIN bookings b             ON c.customer_id  = b.customer_id AND b.booking_status_id = 3
LEFT JOIN customer_points cp     ON c.customer_id  = cp.customer_id
LEFT JOIN customer_subscriptions cs ON c.customer_id = cs.customer_id AND cs.status_id = 1
LEFT JOIN plan_types pt          ON cs.plan_type_id = pt.plan_type_id
GROUP BY c.customer_id, c.full_name, c.phone, c.join_date,
         c.total_spent, cp.total_point, pt.plan_name;

CREATE VIEW vw_care_view AS
SELECT
    b.booking_id, p.pet_name, p.species, p.weight,
    p.health_condition, p.behaviour_note, p.special_requirement,
    r.room_id, rt.type_name AS room_type, r.camera_url,
    c.full_name AS owner_name, c.phone AS owner_phone,
    b.check_in, b.check_out
FROM bookings b
INNER JOIN pets p        ON b.pet_id      = p.pet_id
INNER JOIN customers c   ON b.customer_id  = c.customer_id
INNER JOIN rooms r       ON b.room_id      = r.room_id
INNER JOIN room_types rt ON r.room_type_id = rt.room_type_id
WHERE b.booking_status_id = 2
  AND DATE(b.check_in)  <= CURRENT_DATE
  AND DATE(b.check_out) > CURRENT_DATE;

-- =====================================================
-- 19. INITIAL DEMO DATA (bookings 1-4, manual)
-- Timeline: 2026-02-19 to 2026-05-19 (90 days)
-- =====================================================

INSERT INTO employees (employee_id, full_name, role, phone, base_salary_per_hour) VALUES
(1, 'Nguyễn Văn A', 'manager',  '0900000001', 5000000),
(2, 'Trần Thị B',   'fulltime', '0900000002', 3000000),
(3, 'Lê Văn C',     'parttime', '0900000003', 2000000),
(4, 'Phạm Thị D',   'fulltime', '0900000004', 3500000);

INSERT INTO customers (customer_id, full_name, phone, address, district, join_date) VALUES
(1, 'Nguyễn Văn An', '0912345678', '123 Lê Lợi',        'Quận 1', '2026-02-19'),
(2, 'Trần Thị Bình', '0987654321', '456 Nguyễn Huệ',    'Quận 2', '2026-02-20'),
(3, 'Lê Văn Cường',  '0909123456', '789 Võ Văn Kiệt',   'Quận 5', '2026-02-21');

INSERT INTO customer_points (customer_id, total_point, membership_type, usable_points) VALUES
(1, 0, 'FREE', 0),
(2, 0, 'FREE', 0),
(3, 0, 'FREE', 0);

INSERT INTO customer_subscriptions (customer_id, plan_type_id, start_date, end_date, status_id) VALUES
(1, 1, '2026-02-19', '2026-12-31', 1),
(2, 1, '2026-02-19', '2026-12-31', 1),
(3, 1, '2026-02-19', '2026-12-31', 1);

INSERT INTO pets (pet_id, customer_id, pet_name, species, breed, weight, age, gender, sterilized, vaccinated) VALUES
(1, 1, 'Lucky', 'dog', 'Poodle',            4.5,  2, 'male',   1, 1),
(2, 1, 'Milo',  'dog', 'Corgi',             3.2,  1, 'male',   0, 1),
(3, 2, 'Mimi',  'cat', 'British Shorthair', 3.8,  3, 'female', 0, 1),
(4, 3, 'Max',   'dog', 'Golden',            25.5, 4, 'male',   1, 1);

INSERT INTO attendance (employee_id, work_date, check_in, check_out, working_hours, overtime_hours, penalty) VALUES
(3, '2026-02-19', '2026-02-19 08:00:00', '2026-02-19 17:00:00', 9.0, 1.0, 0),
(3, '2026-02-20', '2026-02-20 13:00:00', '2026-02-20 17:00:00', 4.0, 0.0, 0),
(3, '2026-02-21', '2026-02-21 08:30:00', '2026-02-21 17:00:00', 8.5, 0.5, 50000),
(3, '2026-02-22', '2026-02-22 08:00:00', '2026-02-22 17:00:00', 9.0, 1.0, 0),
(3, '2026-02-23', '2026-02-23 13:00:00', '2026-02-23 17:00:00', 4.0, 0.0, 0),
(2, '2026-02-19', '2026-02-19 08:00:00', '2026-02-19 17:00:00', 9.0, 1.0, 0),
(2, '2026-02-20', '2026-02-20 08:00:00', '2026-02-20 17:00:00', 9.0, 1.0, 0),
(2, '2026-02-21', '2026-02-21 08:00:00', '2026-02-21 17:00:00', 9.0, 1.0, 0),
(4, '2026-02-19', '2026-02-19 07:30:00', '2026-02-19 17:30:00', 10.0, 2.0, 0),
(4, '2026-02-20', '2026-02-20 07:30:00', '2026-02-20 18:00:00', 10.5, 2.5, 0),
(4, '2026-02-21', '2026-02-21 07:30:00', '2026-02-21 18:30:00', 11.0, 3.0, 0),
(4, '2026-02-22', '2026-02-22 08:00:00', '2026-02-22 12:00:00',  4.0, 0.0, 0),
(4, '2026-02-23', '2026-02-23 08:00:00', '2026-02-23 17:00:00',  9.0, 1.0, 0);

INSERT INTO bookings (booking_id, customer_id, pet_id, room_id, check_in, check_out, booking_status_id) VALUES
(1, 1, 1, 1, '2026-02-19 08:00:00', '2026-02-22 08:00:00', 1),
(2, 2, 3, 8, '2026-02-20 08:00:00', '2026-02-23 08:00:00', 1),
(3, 3, 4, 5, '2026-02-21 08:00:00', '2026-02-24 08:00:00', 1),
(4, 1, 2, 2, '2026-02-22 08:00:00', '2026-02-25 08:00:00', 1);

INSERT INTO services (booking_id, pet_id, service_type_id, quantity, service_date, status) VALUES
(1, 1, 1, 2, '2026-02-19', 'done'),
(1, 1, 6, 3, '2026-02-20', 'done'),
(2, 3, 2, 5, '2026-02-20', 'done'),
(2, 3, 5, 1, '2026-02-21', 'done');

INSERT INTO billing (booking_id, total_amount) VALUES
(1, 0), (2, 0), (3, 0), (4, 0);

UPDATE bookings SET booking_status_id = 2 WHERE booking_status_id = 1;
UPDATE bookings SET booking_status_id = 3 WHERE booking_status_id = 2;

-- =====================================================
-- VERIFICATION
-- =====================================================

SELECT '✅ SCHEMA v3 FIXED COMPLETE' AS final_status;
SELECT COUNT(*) AS total_rooms FROM rooms;
-- Expected: 63 rooms (10 original + 53 extended)
-- Attendance timeline: 2026-02-19 to 2026-05-19 (90 days)
-- Bulk attendance (insert_data_v5): 6 employees × 90 days = 540 records
-- =====================================================
-- PET HOTEL - INSERT DATA FIXED v5
-- Timeline: 2026-02-19 to 2026-05-19 (90 days)
-- Bookings: 1500  |  Revenue: ~1 tỷ VNĐ
--
-- FIXES vs v4:
--   [1] booking_seed thêm cột pet_type + type_rn
--       → room assignment dùng slot-based, KHÔNG có double-booking
--   [2] Room IDs mới (11-63) khớp với schema_v3_fixed.sql
--       → original rooms 1-10 giữ nguyên cho demo data
--   [3] Attendance: n < 90
--       (90 ngày: 2026-02-19 đến 2026-05-19 inclusive)
--       Feb(10) + Mar(31) + Apr(30) + May(19) = 90 ngày
--       6 nhân viên × 90 ngày = 540 records
--
-- Room assignment logic (no overlap guaranteed):
--   pet_type   | rooms      | count | slot formula
--   -----------|------------|-------|------------------------------
--   cat        | 46-63      |  18   | room = 46 + MOD(type_rn, 18)
--   small_dog  | 11-34      |  24   | room = 11 + MOD(type_rn, 24)
--   medium_dog | 35-41      |   7   | room = 35 + MOD(type_rn,  7)
--   large_dog  | 42-45      |   4   | room = 42 + MOD(type_rn,  4)
--
--   day_offset = FLOOR(type_rn / room_count) * 3
--   → each room gets 1 booking per 3-day window, zero overlap
--
-- Revenue estimate (after subscription discounts ~3.8%):
--   Room   : ~746M  (685 small×150k + 200 med×250k + 115 large×400k + 500 cat×120k) ×3 nights
--   Service: ~245M  (avg 81,667 base × avg qty 2 × 1500 bookings)
--   Total  : ~991M  ≈ 1 tỷ VNĐ ✓
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SESSION cte_max_recursion_depth = 10000;

-- =========================================================
-- 1. EMPLOYEES (5001-5006)
-- =========================================================

INSERT IGNORE INTO employees (
    employee_id, full_name, role, phone, base_salary_per_hour
) VALUES
(5001, 'Nguyen Minh An',  'manager',  '0950000001', 500000),
(5002, 'Tran Gia Bao',    'fulltime', '0950000002', 350000),
(5003, 'Le Thanh Ha',     'fulltime', '0950000003', 320000),
(5004, 'Pham Quoc Huy',   'parttime', '0950000004', 220000),
(5005, 'Vo Minh Chau',    'fulltime', '0950000005', 340000),
(5006, 'Dang Bao Tram',   'parttime', '0950000006', 210000);

-- =========================================================
-- 2. CUSTOMERS (5001-7000, 2000 customers)
-- =========================================================

INSERT INTO customers (
    customer_id,
    full_name,
    phone,
    address,
    district,
    join_date,
    total_spent
)
WITH RECURSIVE seq AS (
    SELECT 0 AS n
    UNION ALL
    SELECT n + 1
    FROM seq
    WHERE n < 1999
)
SELECT
    5001 + n,
    CONCAT('Customer ', n + 1),
    CONCAT('09', LPAD(n + 1, 8, '0')),
    CONCAT(n + 1, ' Nguyen Trai'),
    CONCAT('District ', 1 + MOD(n, 12)),
    DATE_ADD('2026-02-19', INTERVAL MOD(n, 89) DAY),
    0
FROM seq;

-- =========================================================
-- 3. CUSTOMER POINTS
-- =========================================================

INSERT INTO customer_points (customer_id, total_point, membership_type, usable_points)
SELECT customer_id, 0, 'FREE', 0
FROM customers
WHERE customer_id >= 5001;

-- =========================================================
-- 4. PETS (8001-10000, 2000 pets)
--    Weight distribution (1500 used in booking_seed):
--      MOD(n,3)=0            → cat,        weight 4   (~500 cats)
--      dog, MOD(n,5)=0       → medium dog, weight 10  (~200)
--      dog, MOD(n,7)=0       → large dog,  weight 20  (~115)
--      dog, else             → small dog,  weight 3   (~685)
-- =========================================================

INSERT INTO pets (
    pet_id,
    customer_id,
    pet_name,
    species,
    breed,
    weight,
    age,
    gender,
    sterilized,
    vaccinated
)
WITH RECURSIVE seq AS (
    SELECT 0 AS n
    UNION ALL
    SELECT n + 1
    FROM seq
    WHERE n < 1999
)
SELECT
    8001 + n,
    5001 + n,
    CASE
        WHEN MOD(n, 3) = 0 THEN CONCAT('Cat_', n)
        ELSE CONCAT('Dog_', n)
    END,
    CASE
        WHEN MOD(n, 3) = 0 THEN 'cat'
        ELSE 'dog'
    END,
    CASE
        WHEN MOD(n, 3) = 0 THEN 'British Shorthair'
        WHEN MOD(n, 2) = 0 THEN 'Poodle'
        ELSE 'Corgi'
    END,
    CASE
        WHEN MOD(n, 3) = 0 THEN 4
        WHEN MOD(n, 5) = 0 THEN 10
        WHEN MOD(n, 7) = 0 THEN 20
        ELSE 3
    END,
    2 + MOD(n, 8),
    CASE
        WHEN MOD(n, 2) = 0 THEN 'male'
        ELSE 'female'
    END,
    1,
    1
FROM seq;

-- =========================================================
-- 5. SUBSCRIPTIONS (2000)
--    Discount distribution (customer_id 5001-7000):
--      MOD(id,10)=0 → Platinum (15%) : 10% customers
--      MOD(id, 5)=0 → Gold     (10%) : 10% customers (id%10≠0)
--      MOD(id, 3)=0 → Silver   ( 5%) : ~27% customers (id%5≠0)
--      else         → Standard ( 0%) : ~53% customers
--    Weighted avg discount ≈ 3.83%
-- =========================================================

INSERT INTO customer_subscriptions (customer_id, plan_type_id, start_date, end_date, status_id)
SELECT
    customer_id,
    CASE WHEN MOD(customer_id, 10) = 0 THEN 4   -- Platinum
         WHEN MOD(customer_id,  5) = 0 THEN 3   -- Gold
         WHEN MOD(customer_id,  3) = 0 THEN 2   -- Silver
         ELSE 1 END,                              -- Standard
    '2026-02-19', '2026-12-31', 1
FROM customers WHERE customer_id >= 5001;

-- =========================================================
-- DROP double-booking trigger for bulk insert
-- =========================================================

DROP TRIGGER IF EXISTS trg_prevent_double_booking;

-- =========================================================
-- 6. BOOKING SEED
--    Adds pet_type + type_rn (0-based rank within same type)
--    to drive non-overlapping room + day assignment
-- =========================================================

CREATE TEMPORARY TABLE booking_seed AS
SELECT
    ROW_NUMBER() OVER (ORDER BY p.pet_id)  AS rn,
    p.pet_id,
    p.customer_id,
    p.species,
    p.weight,
    -- Classify pet type for room routing
    CASE
        WHEN p.species = 'cat'             THEN 'cat'
        WHEN p.weight < 5                  THEN 'small_dog'
        WHEN p.weight BETWEEN 5 AND 15     THEN 'medium_dog'
        ELSE                                    'large_dog'
    END AS pet_type,
    -- 0-based rank within each pet_type (drives slot calculation)
    ROW_NUMBER() OVER (
        PARTITION BY
            CASE
                WHEN p.species = 'cat'         THEN 'cat'
                WHEN p.weight < 5              THEN 'small_dog'
                WHEN p.weight BETWEEN 5 AND 15 THEN 'medium_dog'
                ELSE                                'large_dog'
            END
        ORDER BY p.pet_id
    ) - 1 AS type_rn
FROM pets p
WHERE p.pet_id >= 8001
LIMIT 1500;

-- =========================================================
-- 7. BOOKINGS (9001-10500)
--
-- Non-overlap guarantee:
--   Each room_count-sized batch shares the SAME 3-day window.
--   Next batch starts 3 days later → no two bookings in same
--   room ever overlap.
--
--   room_count values:
--     cat       → 18  rooms (46-63)
--     small_dog → 24  rooms (11-34)
--     medium_dog →  7 rooms (35-41)
--     large_dog  →  4 rooms (42-45)
--
--   Max day_offset per type (all ≤ 84 → check_out ≤ day 87 < 90):
--     cat:        FLOOR(499/18)*3 = 27*3 = 81
--     small_dog:  FLOOR(684/24)*3 = 28*3 = 84
--     medium_dog: FLOOR(199/ 7)*3 = 28*3 = 84
--     large_dog:  FLOOR(114/ 4)*3 = 28*3 = 84
-- =========================================================

INSERT INTO bookings (booking_id, customer_id, pet_id, room_id, check_in, check_out, booking_status_id, notes)
SELECT
    9000 + rn,
    customer_id,
    pet_id,
    -- Room assignment: base_room + slot within room_count
    CASE pet_type
        WHEN 'cat'         THEN 46 + MOD(type_rn, 18)
        WHEN 'small_dog'   THEN 11 + MOD(type_rn, 24)
        WHEN 'medium_dog'  THEN 35 + MOD(type_rn,  7)
        WHEN 'large_dog'   THEN 42 + MOD(type_rn,  4)
    END,
    -- check_in: day_offset = FLOOR(type_rn / room_count) * 3
    DATE_ADD('2026-02-19 08:00:00',
        INTERVAL (FLOOR(type_rn /
            CASE pet_type
                WHEN 'cat'        THEN 18
                WHEN 'small_dog'  THEN 24
                WHEN 'medium_dog' THEN  7
                ELSE                    4
            END
        ) * 3) DAY
    ),
    -- check_out: check_in + 3 days
    DATE_ADD(
        DATE_ADD('2026-02-19 08:00:00',
            INTERVAL (FLOOR(type_rn /
                CASE pet_type
                    WHEN 'cat'        THEN 18
                    WHEN 'small_dog'  THEN 24
                    WHEN 'medium_dog' THEN  7
                    ELSE                    4
                END
            ) * 3) DAY
        ),
        INTERVAL 3 DAY
    ),
    1,
    CONCAT('Auto booking #', 9000 + rn)
FROM booking_seed;

-- =========================================================
-- 8. SERVICES (1500)
--    service_type_id cycles 1-6, quantity cycles 1-3
--    Avg revenue per booking ≈ 163,333 VNĐ
-- =========================================================

INSERT INTO services (booking_id, pet_id, service_type_id, quantity, service_date, status)
SELECT
    b.booking_id,
    b.pet_id,
    1 + MOD(b.booking_id, 6),
    1 + MOD(b.booking_id, 3),
    DATE(b.check_in),
    'done'
FROM bookings b
WHERE b.booking_id >= 9001;

-- =========================================================
-- 9. BILLING (1500)
--    total_amount computed AFTER services are inserted
--    payment_date = check_out + 1 hour
-- =========================================================

INSERT INTO billing (booking_id, employee_id, total_amount, discount_amount, payment_method_id, payment_date)
SELECT
    b.booking_id,
    5001 + MOD(b.booking_id, 6),
    calculate_booking_total_v2(b.booking_id),
    0,
    1 + MOD(b.booking_id, 3),
    DATE_ADD(b.check_out, INTERVAL 1 HOUR)
FROM bookings b
WHERE b.booking_id >= 9001;

-- =========================================================
-- 10. STATUS FLOW: 1 → 2 → 3
--     trg_validate_booking_status allows: 1→2, 2→3
--     trg_award_points fires on →3 (1500 point_transactions)
-- =========================================================

UPDATE bookings SET booking_status_id = 2 WHERE booking_status_id = 1 AND booking_id >= 9001;
UPDATE bookings SET booking_status_id = 3 WHERE booking_status_id = 2 AND booking_id >= 9001;

-- =========================================================
-- RECREATE double-booking trigger
-- =========================================================

DELIMITER //

CREATE TRIGGER trg_prevent_double_booking
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM bookings b
        WHERE b.room_id           = NEW.room_id
          AND b.booking_status_id IN (1, 2)
          AND b.check_in          < NEW.check_out
          AND b.check_out         > NEW.check_in
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Room already booked for selected period';
    END IF;
END //

DELIMITER ;

-- =========================================================
-- 11. UPDATE CUSTOMER TOTAL SPENT
-- =========================================================

UPDATE customers c
JOIN (
    SELECT b.customer_id, SUM(bl.total_amount) AS total_spent
    FROM bookings b
    JOIN billing bl ON b.booking_id = bl.booking_id
    WHERE b.booking_id >= 9001
    GROUP BY b.customer_id
) x ON c.customer_id = x.customer_id
SET c.total_spent      = x.total_spent,
    c.last_active_date = CURRENT_DATE
WHERE c.customer_id >= 5001;

-- =========================================================
-- 12. ATTENDANCE
--     Timeline: 2026-02-19 to 2026-05-19 inclusive = 90 ngày
--       Feb(10) + Mar(31) + Apr(30) + May(19) = 90 ngày
--       n=0 → 2026-02-19, n=89 → 2026-05-19  → cần n < 90
--     6 employees × 90 days = 540 records
-- =========================================================

INSERT INTO attendance (
    employee_id,
    work_date,
    check_in,
    check_out,
    working_hours,
    overtime_hours,
    penalty
)
WITH RECURSIVE seq AS (
    SELECT 0 AS n
    UNION ALL
    SELECT n + 1
    FROM seq
    WHERE n < 89
)
SELECT
    e.employee_id,
    DATE_ADD('2026-02-19', INTERVAL seq.n DAY),
    CONCAT(DATE_ADD('2026-02-19', INTERVAL seq.n DAY), ' 08:00:00'),
    CONCAT(DATE_ADD('2026-02-19', INTERVAL seq.n DAY), ' 17:00:00'),
    9.0,
    CASE
        WHEN MOD(seq.n, 5) = 0 THEN 1.0
        ELSE 0.0
    END,
    0
FROM employees e
CROSS JOIN seq
WHERE e.employee_id >= 5001;

-- =========================================================
-- CLEANUP
-- =========================================================

DROP TEMPORARY TABLE IF EXISTS booking_seed;
SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- VERIFICATION
-- =========================================================

SELECT '=== RECORD COUNTS ===' AS info;
SELECT 'customers'  AS tbl, COUNT(*) AS cnt FROM customers  WHERE customer_id >= 5001
UNION ALL SELECT 'pets',       COUNT(*) FROM pets        WHERE pet_id      >= 8001
UNION ALL SELECT 'bookings',   COUNT(*) FROM bookings    WHERE booking_id  >= 9001
UNION ALL SELECT 'services',   COUNT(*) FROM services    WHERE booking_id  >= 9001
UNION ALL SELECT 'billing',    COUNT(*) FROM billing     WHERE booking_id  >= 9001
UNION ALL SELECT 'attendance', COUNT(*) FROM attendance  WHERE employee_id >= 5001;
-- Expected attendance: 540 (6 × 90 days)

SELECT '=== TIMELINE ===' AS info;
SELECT
    MIN(DATE(check_in))  AS earliest_checkin,
    MAX(DATE(check_out)) AS latest_checkout
FROM bookings WHERE booking_id >= 9001;
-- Expected: 2026-02-19 to ≤ 2026-05-19

SELECT '=== DOUBLE BOOKING CHECK ===' AS info;
SELECT COUNT(*) AS overlap_count
FROM bookings b1
JOIN bookings b2 ON b1.room_id   = b2.room_id
                AND b1.booking_id < b2.booking_id
                AND b1.check_in   < b2.check_out
                AND b1.check_out  > b2.check_in
WHERE b1.booking_id >= 9001 AND b2.booking_id >= 9001;
-- Expected: 0 (zero overlaps)

SELECT '=== REVENUE ===' AS info;
SELECT
    ROUND(SUM(total_amount) / 1000000000, 3) AS billion_vnd,
    COUNT(*)                                  AS invoices,
    ROUND(AVG(total_amount), 0)               AS avg_per_booking
FROM billing WHERE booking_id >= 9001;
-- Expected: ~0.991 billion VNĐ (~1 tỷ)

SELECT '=== REVENUE BY MONTH ===' AS info;
SELECT
    DATE_FORMAT(payment_date, '%Y-%m') AS month,
    COUNT(*)                           AS invoices,
    ROUND(SUM(total_amount)/1000000,0) AS million_vnd
FROM billing
WHERE booking_id >= 9001
GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
ORDER BY month;

SELECT '=== ROOM DISTRIBUTION (no overlaps) ===' AS info;
SELECT
    r.room_id,
    rt.type_name,
    COUNT(b.booking_id) AS bookings,
    MIN(DATE(b.check_in))  AS first_checkin,
    MAX(DATE(b.check_out)) AS last_checkout
FROM rooms r
JOIN room_types rt ON r.room_type_id = rt.room_type_id
LEFT JOIN bookings b ON r.room_id = b.room_id AND b.booking_id >= 9001
WHERE r.room_id BETWEEN 11 AND 63
GROUP BY r.room_id, rt.type_name
ORDER BY r.room_id;

SELECT '=== ATTENDANCE TIMELINE ===' AS info;
SELECT
    MIN(work_date) AS first_day,
    MAX(work_date) AS last_day,
    COUNT(*)       AS total_records
FROM attendance WHERE employee_id >= 5001;
-- Expected: 2026-02-19 to 2026-05-19, 540 records (6 × 90 days)

SELECT '=== STATUS ===' AS info;
SELECT bs.status_name, COUNT(*) AS cnt
FROM bookings b
JOIN booking_statuses bs ON b.booking_status_id = bs.status_id
WHERE b.booking_id >= 9001
GROUP BY bs.status_name;

SELECT '✅ INSERT DATA v5 FIXED COMPLETE - 2026-02-19 to 2026-05-19' AS final_status;

SELECT * from customer_subscriptions;

