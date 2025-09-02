from streamlit_authenticator.utilities.hasher import Hasher

# Vul hier je wachtwoorden in (1 of meer):
passwords = ["user"]

# Eén hash:
print(Hasher.hash(passwords[0]))

# Of meerdere in lijst:
# print(Hasher.hash_list(passwords))
