class AuthMessages:
    # Success
    SIGNUP_SUCCESS = "Account created successfully. Please check your email for the OTP."
    OTP_SENT = "A verification code has been sent to your email."
    OTP_VERIFIED = "Your email has been verified successfully."
    LOGIN_SUCCESS = "Login successful. Welcome back!"
    LOGOUT_SUCCESS = "You have been logged out successfully."
    PASSWORD_RESET_SUCCESS = "Your password has been reset successfully."

    # Errors
    EMAIL_EXISTS = "This email is already registered."
    INVALID_EMAIL = "No account found with this email."
    INVALID_PASSWORD = "Incorrect password. Please try again."
    EMAIL_NOT_VERIFIED = "Please verify your email before logging in."
    OTP_INVALID = "Invalid or expired OTP."
    OTP_ALREADY_VERIFIED = "This email is already verified."
    GENERIC_ERROR = "Something went wrong. Please try again."