-- Run after the grant, with buba logged out. Restore the ordinary status required by Enable.
USE [GameDB];
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF (SELECT COUNT_BIG(*) FROM dbo.[character] WHERE cha_name = 'buba') <> 1
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51000, 'Expected exactly one character named buba; nothing changed.', 1;
END;
UPDATE a SET gm = 0
FROM dbo.account AS a
WHERE a.gm = 99 AND a.act_id = (
    SELECT c.act_id FROM dbo.[character] AS c WHERE c.cha_name = 'buba'
);
IF @@ROWCOUNT <> 1
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51002, 'Expected one account with temporary gm=99; nothing changed.', 1;
END;
COMMIT TRANSACTION;
SELECT 'Ordinary status restored for the account of buba. Log in again.' AS result;
