use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;
use anyhow::{Result, anyhow};
use base64::Engine;
use ironcore_alloy::standalone::config::{
    RotatableSecret, StandaloneConfiguration, StandaloneSecret, StandardSecrets, VectorSecret,
};
use ironcore_alloy::standard_attached::StandardAttachedDocumentOps;
use ironcore_alloy::vector::{PlaintextVector, PlaintextVectors, VectorOps, VectorId};
use ironcore_alloy::{AlloyMetadata, DerivationPath, Secret, SecretPath, Standalone, TenantId};

use qdrant_client::qdrant::{
    CreateCollectionBuilder, PointStruct, QueryPointsBuilder, UpsertPointsBuilder, Value as QdrantValue,
    Distance, Query, VectorParamsBuilder,Condition,Filter,
};
use qdrant_client::qdrant::with_payload_selector::SelectorOptions;
use qdrant_client::{Qdrant, Payload};
use tokenizers::tokenizer::Tokenizer;
use serde_json::{self, json, Value};

const ENCRYPTED_DOC_KEY: &str = "_encrypted_document";
const EMBEDDING_DIMENSION: u64 = 100;





struct AppResources {
    tokenizer: Tokenizer,
    client: Qdrant,
    alloy_client: Arc<Standalone>,
    base64_engine: base64::engine::GeneralPurpose,
}




impl AppResources {
    fn new() -> Result<Self> {
        let tokenizer = Tokenizer::from_file("src/tokenizer.json")
            .map_err(|e| anyhow!("Failed to load tokenizer: {}", e))?;
        let client = Qdrant::from_url("http://localhost:6334").build()?;
        let alloy_client = create_alloy_client()?;
        let base64_engine = base64::engine::general_purpose::STANDARD_NO_PAD;

        Ok(AppResources {
            tokenizer,
            client,
            alloy_client,
            base64_engine,
        })
    }
}

fn create_alloy_client() -> Result<Arc<Standalone>> {
    let standalone_secret =
        hex_literal::hex!("f8cba200fb44b891d6a389858ae699d57b7ff48572cdcb9e5ed1d4364bf531b8");
    let config = StandaloneConfiguration::new(
        StandardSecrets::new(
            Some(1),
            vec![StandaloneSecret::new(
                1,
                Secret::new(standalone_secret.to_vec())?,
            )],
        )?,
        Default::default(),
        HashMap::from([(
            SecretPath("".to_string()),
            VectorSecret::new(
                2.0,
                RotatableSecret::new(
                    Some(StandaloneSecret::new(
                        1,
                        Secret::new(standalone_secret.to_vec())?,
                    )),
                    None,
                )?,
            ),
        )]),
    );

    Ok(ironcore_alloy::Standalone::new(&config))
}

async fn run_app(resources: AppResources) -> Result<()> {
    let tenant_name: &str = "003";
    let tenant_id: TenantId = TenantId(tenant_name.to_string());
    let alloy_metadata = AlloyMetadata::new_simple(tenant_id);

    // Create collection
    let collection_creation_result = resources.client.create_collection(
        CreateCollectionBuilder::new(tenant_name)
            .vectors_config(VectorParamsBuilder::new(EMBEDDING_DIMENSION, Distance::Cosine))
    ).await;

    match collection_creation_result {
        Ok(_) => println!("Collection '{}' created successfully.", tenant_name),
        Err(e) if e.to_string().contains("already exists") => {
            println!("Collection '{}' already exists. Proceeding with data insertion.", tenant_name);
        }
        Err(e) => {
            return Err(anyhow!("Failed to create collection '{}': {}", tenant_name, e));
        }
    }
    


    let data = vec![
            json!( {
                "title": "The Hobbit",
                "description": "The Hobbit, or There and Back Again, is a children's fantasy novel by J. R. R. Tolkien, published in 1937. It is set in the same world as The Lord of the Rings."
            }),
            json!( {
                "title": "Harry Potter and the Philosopher's Stone",
                "description": "The first book in the Harry Potter series by J.K. Rowling, following the life and adventures of a young wizard, Harry Potter, as he attends Hogwarts School of Witchcraft and Wizardry."
            }),
            json!( {
                "title": "The Chronicles of Narnia: The Lion, the Witch and the Wardrobe",
                "description": "A fantasy novel by C.S. Lewis, this book tells the story of four siblings who discover the magical land of Narnia and the epic battle between good and evil."
            }),
            json!( {
                "title": "Good Omens",
                "description": "A comedic fantasy novel by Neil Gaiman and Terry Pratchett, focusing on the unlikely partnership between an angel and a demon who team up to prevent the apocalypse."
            }),
            json!( {
                "title": "1984",
                "description": "A dystopian social science fiction novel and cautionary tale by the English writer George Orwell, published in 1949."
            }),
            json!( {
                "title": "Brave New World",
                "description": "A dystopian novel written by Aldous Huxley in 1931, and published in 1932."
            }),
            json!( {
                "title": "Fahrenheit 451",
                "description": "A dystopian novel by Ray Bradbury published in 1953 that presents a future American society where books are outlawed and 'firemen' burn any that are found."
            }),
            json!( {
                "title": "The Great Gatsby",
                "description": "A 1925 novel written by American author F. Scott Fitzgerald that follows a cast of characters living in the fictional towns of West Egg and East Egg on prosperous Long Island."
            }),
            json!( {
                "title": "Moby-Dick",
                "description": "An 1851 novel by Herman Melville, which narrates the quest of Ahab, captain of the whaling ship Pequod, for revenge against Moby Dick, a white whale."
            }),
            json!( {
                "title": "War and Peace",
                "description": "A historical novel by Leo Tolstoy, published in 1869, that tells the story of five families against the backdrop of Napoleon's invasion of Russia."
            }),
            json!( {
                "title": "The Catcher in the Rye",
                "description": "A novel by J. D. Salinger, published in 1951, that follows the experiences of 16-year-old Holden Caulfield after he is expelled from his prep school."
            }),
            json!( {
                "title": "To Kill a Mockingbird",
                "description": "A novel by Harper Lee published in 1960, which is widely regarded as a classic of modern American literature. The novel is renowned for its warmth and humor, despite dealing with serious issues of rape and racial inequality."
            }),
            json!( {
                "title": "Pride and Prejudice",
                "description": "A romantic novel by Jane Austen, published in 1813, that charts the emotional development of the protagonist Elizabeth Bennet as she deals with issues of manners, upbringing, morality, and marriage."
            }),
            json!( {
                "title": "The Lord of the Rings: The Fellowship of the Ring",
                "description": "The first volume of J.R.R. Tolkien's The Lord of the Rings, published in 1954, which follows the journey of Frodo Baggins to destroy the One Ring."
            }),
            json!( {
                "title": "Jane Eyre",
                "description": "A novel by Charlotte Brontë, published in 1847, which follows the emotions and experiences of its eponymous heroine, including her growth to adulthood and her love for Mr. Rochester."
            }),
            json!( {
                "title": "The Picture of Dorian Gray",
                "description": "A novel by Oscar Wilde, published in 1890, which follows the young and beautiful Dorian Gray as he embarks on a life of hedonism, while his portrait ages and shows the marks of his sins."
            }),
            json!( {
                "title": "Frankenstein",
                "description": "A novel by Mary Shelley, published in 1818, which tells the story of Victor Frankenstein, a scientist who creates a sapient creature in an unorthodox experiment."
            }),
            json!( {
                "title": "Dracula",
                "description": "An 1897 Gothic horror novel by Irish author Bram Stoker, introducing the character of Count Dracula and establishing many conventions of subsequent vampire fantasy."
            }),
            json!( {
                "title": "Wuthering Heights",
                "description": "A novel by Emily Brontë, published in 1847, that revolves around the passionate and doomed love between Catherine Earnshaw and Heathcliff."
            }),
            json!( {
                "title": "The Odyssey",
                "description": "An ancient Greek epic poem attributed to Homer, which follows the Greek hero Odysseus on his long journey home after the fall of Troy."
            }),
            json!( {
                "title": "Don Quixote",
                "description": "A Spanish novel by Miguel de Cervantes, published in two parts in 1605 and 1615. It is considered one of the most influential works of literature from the Spanish Golden Age."
            }),
            json!( {
                "title": "The Brothers Karamazov",
                "description": "A novel by Fyodor Dostoevsky, published in 1880, which is a passionate philosophical novel that explores deep ethical debates about God, free will, and morality."
            }),
            json!( {
                "title": "Crime and Punishment",
                "description": "A novel by Fyodor Dostoevsky, published in 1866, that focuses on the mental anguish and moral dilemmas of Rodion Raskolnikov, a poor ex-student who plans to murder a pawnbroker."
            }),
            json!( {
                "title": "Anna Karenina",
                "description": "A novel by Leo Tolstoy, published in 1877, which tells the tragic love story of Anna Karenina, set against the backdrop of Russian society."
            }),
            json!( {
                "title": "One Hundred Years of Solitude",
                "description": "A novel by Colombian author Gabriel García Márquez, published in 1967, which tells the multi-generational story of the Buendía family and their town, Macondo."
            }),
            json!( {
                "title": "The Sound and the Fury",
                "description": "A novel by William Faulkner, published in 1929, that presents a family in decline and employs stream-of-consciousness writing to narrate their history."
            }),
            json!( {
                "title": "Ulysses",
                "description": "A modernist novel by James Joyce, first serialized in 1918-1920, which chronicles the experiences of Leopold Bloom in Dublin during a single day, June 16, 1904."
            }),
            json!( {
                "title": "The Divine Comedy",
                "description": "An epic poem by Dante Alighieri, written between 1308 and 1320, which takes readers on a journey through Hell, Purgatory, and Paradise."
            }),
            json!( {
                "title": "Les Misérables",
                "description": "A French historical novel by Victor Hugo, first published in 1862, that follows the lives and interactions of several characters, particularly ex-convict Jean Valjean, against the backdrop of post-Revolutionary France."
            }),
            json!( {
                "title": "Madame Bovary",
                "description": "A novel by Gustave Flaubert, published in 1857, that portrays the life of Emma Bovary and her pursuit of romantic fantasies, ultimately leading to her downfall."
            }),
            json!( {
                "title": "The Iliad",
                "description": "An ancient Greek epic poem attributed to Homer, set during the Trojan War and focusing on the hero Achilles."
            }),
            json!( {
                "title": "Moby-Dick",
                "description": "An 1851 novel by Herman Melville, about Captain Ahab's obsessive quest to kill the white whale, Moby Dick."
            }),
            json!( {
                "title": "The Grapes of Wrath",
                "description": "A novel by John Steinbeck, published in 1939, that focuses on the plight of poor tenant farmers displaced by the Dust Bowl."
            }),
            json!( {
                "title": "Catch-22",
                "description": "A satirical novel by Joseph Heller, published in 1961, that follows a group of World War II bomber pilots and the absurdity of military bureaucracy."
            }),
            json!( {
                "title": "The Stranger",
                "description": "A novel by Albert Camus, published in 1942, that tells the story of Meursault, a man who is indifferent to social conventions and events, and his trial for the murder of an Arab."
            }),
            json!( {
                "title": "Beloved",
                "description": "A novel by Toni Morrison, published in 1987, which explores the psychological and physical trauma of slavery in America, focusing on the life of Sethe, a former enslaved woman."
            }),
            json!( {
                "title": "Slaughterhouse-Five",
                "description": "A satirical novel by Kurt Vonnegut, published in 1969, which tells the story of Billy Pilgrim, who becomes 'unstuck in time' and experiences moments from his life, including the firebombing of Dresden."
            }),
            json!( {
                "title": "The Road",
                "description": "A post-apocalyptic novel by Cormac McCarthy, published in 2006, that follows a father and son as they struggle to survive in a world ravaged by disaster."
            }),
            json!( {
                "title": "Lolita",
                "description": "A controversial novel by Vladimir Nabokov, published in 1955, that tells the story of Humbert Humbert and his obsession with a 12-year-old girl named Dolores Haze."
            }),
            json!( {
                "title": "The Handmaid's Tale",
                "description": "A dystopian novel by Margaret Atwood, published in 1985, that presents a future where women are subjugated under a theocratic dictatorship."
            })
        ];


    let points: Vec<_> = futures::future::try_join_all(
        data.into_iter().map(|book_json| {
            let desc = book_json["description"].as_str().unwrap_or_default();
            generate_simple_embedding_and_encrypt_point(
                resources.alloy_client.clone(),
                &alloy_metadata,
                &resources.tokenizer,
                book_json.clone(),
                desc.to_string(),
            )
        })
    ).await?;

    // for point in &points {

    //     println!("Encrypted Vector: {:?}", point.vectors); // Print the encrypted vector
    //     println!("Payload: {:?}", point.payload); // Print the payload
    // }
    // Insert points
    resources.client.upsert_points(
        UpsertPointsBuilder::new(tenant_name, points)
            .wait(true)
    ).await?;






    // Perform a search
    let query_text = "Name the book written by Neil Gaiman";
    let query_embedding = generate_simple_embedding(&resources.tokenizer, query_text)?;

    let mut query_vectors = resources.alloy_client
        .vector()
        .generate_query_vectors(
            PlaintextVectors(
                HashMap::from([(VectorId("".to_string()), create_plaintext_vector(&query_embedding))])
            ),
            &alloy_metadata,
        )
        .await?;

    let query_vector = query_vectors
        .0
        .remove(&VectorId("".to_string()))
        .ok_or_else(|| anyhow!("No query vector generated"))?
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("Empty query vector list"))?;

    let filter = Filter::must([Condition::matches("title", "Good Omens".to_string())]);

    let start_time = Instant::now();

    let search_result = resources.client
        .query(
            QueryPointsBuilder::new(tenant_name)
                .query(Query::new_nearest(query_vector.encrypted_vector))
                .with_payload(true)
                // .with_payload(SelectorOptions::Include(
                //     vec![
                //         "description".to_string(),
                //         // "village".to_string(),
                //         // "town".to_string(),
                //     ]
                //     .into(),
                // ))

                // .with_payload(SelectorOptions::Exclude(vec!["title".to_string()].into()))
                // .filter(filter.clone())
                // .build()
                // .with_vectors(true)
        )
        .await?;

    let elapsed_time = start_time.elapsed();


    dbg!(&search_result);
    for found_point in search_result.result.into_iter() {
        let mut payload = found_point.payload;

        // Extract and print the title if available
        if let Some(title_value) = payload.remove("title") {
            if let Some(title) = title_value.as_str() {
                println!("Title: {}", title);
            }
        }

        // Process the encrypted document
        if let Some(encrypted_payload) = payload.remove(ENCRYPTED_DOC_KEY) {
            if let Some(encrypted_str) = encrypted_payload.as_str() {
                let encrypted_bytes = resources.base64_engine.decode(encrypted_str)?;
                let decrypted_document = resources.alloy_client
                    .standard_attached()
                    .decrypt(
                        ironcore_alloy::standard_attached::EncryptedAttachedDocument(
                            ironcore_alloy::EncryptedBytes(encrypted_bytes)
                        ),
                        &alloy_metadata,
                    )
                    .await?;
                println!(
                    "Decrypted document: {}",
                    std::str::from_utf8(&decrypted_document.0.0)?
                );
            }
        }
    }
    println!("Time taken for search: {:?}", elapsed_time);

    Ok(())
}

fn main() -> Result<()> {
    let start_time = Instant::now();
    let resources = AppResources::new()?;
    let runtime = tokio::runtime::Runtime::new()?;
    runtime.block_on(run_app(resources))?;
    let elapsed_time = start_time.elapsed();
    println!("Time taken for the program to execute: {:?}", elapsed_time);
    Ok(())
}

// Helper functions remain mostly the same
fn generate_simple_embedding(tokenizer: &Tokenizer, text: &str) -> Result<Vec<f32>> {
    let encoding = tokenizer.encode(text, true)
        .map_err(|e| anyhow!("Failed to encode text: {}", e))?;
    let ids = encoding.get_ids();

    let mut embedding = vec![0.0; EMBEDDING_DIMENSION as usize];
    for (i, &id) in ids.iter().enumerate() {
        embedding[i % (EMBEDDING_DIMENSION as usize)] += id as f32;
    }

    let magnitude: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
    if magnitude > 0.0 {
        for x in &mut embedding {
            *x /= magnitude;
        }
    }

    Ok(embedding)
}

async fn generate_simple_embedding_and_encrypt_point(
    alloy_client: Arc<Standalone>,
    alloy_metadata: &AlloyMetadata,
    tokenizer: &Tokenizer,
    book_json: Value,
    text: String,
) -> Result<PointStruct> {
    let embedding = generate_simple_embedding(tokenizer, &text)?;

    // Print the original vector
    // println!("Original vector: {:?}", embedding);

    let encrypted_json = alloy_client
        .standard_attached()
        .encrypt(
            ironcore_alloy::standard_attached::PlaintextAttachedDocument(
                ironcore_alloy::PlaintextBytes(
                    serde_json::to_string(&book_json)
                        .map_err(|e| anyhow!("Failed to serialize JSON: {}", e))?
                        .as_bytes()
                        .to_vec()
                )
            ),
            &alloy_metadata,
        )
        .await?;

    let encrypted_vector = alloy_client
        .vector()
        .encrypt(create_plaintext_vector(&embedding), &alloy_metadata)
        .await?;

    // Print the encrypted vector
    // println!("Encrypted vector: {:?}", encrypted_vector.encrypted_vector);

    let mut payload = Payload::new();
    let encoded_string = base64::engine::general_purpose::STANDARD_NO_PAD.encode(encrypted_json.0);

    payload.insert(
        ENCRYPTED_DOC_KEY.to_string(),
        QdrantValue::from(encoded_string),
    );

    if let Some(title) = book_json["title"].as_str() {
        payload.insert("title".to_string(), QdrantValue::from(title));
    }
    Ok(PointStruct::new(
        uuid::Uuid::new_v4().to_string(),
        encrypted_vector.encrypted_vector,
        payload,
    ))
}

fn create_plaintext_vector(v: &[f32]) -> PlaintextVector {
    PlaintextVector {
        plaintext_vector: v.to_vec(),
        secret_path: SecretPath("".to_string()),
        derivation_path: DerivationPath("".to_string()),
    }
}