-- Run while buba is logged out. Changes only the account linked to exact character buba.
USE [GameDB];
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF (SELECT COUNT_BIG(*) FROM dbo.[character] WHERE cha_name = 'buba') <> 1
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51000, 'Expected exactly one character named buba; nothing changed.', 1;
END;
UPDATE a SET gm = 99
FROM dbo.account AS a
WHERE a.gm = 0 AND a.act_id = (
    SELECT c.act_id FROM dbo.[character] AS c WHERE c.cha_name = 'buba'
);
IF @@ROWCOUNT <> 1
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51001, 'Expected one ordinary account with gm=0; nothing changed.', 1;
END;
COMMIT TRANSACTION;
SELECT 'Temporary GM enabled for the account of buba. Log in again. Restore gm=0 after grant.' AS result;
