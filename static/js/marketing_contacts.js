document.addEventListener('DOMContentLoaded', function() {
    const contactList = document.getElementById('contact-list');
    const addContactForm = document.getElementById('add-contact-form');

    function loadContacts() {
        fetch('/marketing/api/contacts')
            .then(response => response.json())
            .then(contacts => {
                contactList.innerHTML = contacts.map(contact => `
                    <div>
                        ${contact.name} - ${contact.email} - ${contact.company || 'N/A'}
                        ${contact.subscribed ? 'Suscrito' : 'No suscrito'}
                    </div>
                `).join('');
            });
    }

    addContactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('contact-name').value;
        const email = document.getElementById('contact-email').value;
        const company = document.getElementById('contact-company').value;

        fetch('/marketing/api/contacts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, company }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            loadContacts();
            addContactForm.reset();
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });

    loadContacts();
});